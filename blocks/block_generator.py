import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from exception.missing_api_key_error import MissingAPIKeyError

class BlockGenerator:
    """
    OpenAI API 客戶端類別，用於用使用者輸入產生 block
    """
    
    def __init__(self, api_key: str = None):
        """
        初始化 OpenAI 客戶端
        """

        self.app_id = "openai"
        self.system_prompt = self._get_default_system_prompt()
        self.api_key = self._get_api_key()
        self.client = OpenAI(api_key=self.api_key)
    
    def _get_default_system_prompt(self) -> str:
        """
        取得預設的系統提示詞
        
        Returns:
            str: 預設系統提示詞
        """
        return (
            "你需要根據使用者的輸入生成一個 python class，用來使用使用者要求的服務的 API。"
            "class 須包含 app_id，例如 'com.openai'。"
            "在 init 方法中，輸入 api key 以及其他必要參數，並且確保 app_id 已經定義。"
            "class 中可以包含數個方法，用來執行特定 API，例如 send_message()、create_page() 等等，請根據使用者指示生成方法"
            "可以上網查詢相關的 API 文檔，並根據文檔生成方法的實現。"
            "請注意一些常見的細節，例如可能需要指定 User-Agent、Content-Type 等 HTTP 標頭。"
            "盡量使用 python 標準庫實現，盡量避免使用 pip install。"
            "請確保生成的 class 可以正常運行，並且能夠處理可能的錯誤情況。"
            "並且生成良好的註釋，包括方法的參數、返回值、可能的錯誤等資訊。"
            "並且盡量遵循 PEP8 的 code style guide，保持代碼的可讀性和一致性。"
            "使用者可能會提到 block 這個關鍵字，這是前端的用語，對應到後端就是 class 的概念。"
            "不需要輸出使用範例或任何其他資訊以及符號，包括 code block 的符號，輸出結果應該是純粹的 Python class 定義。"
        )
    
    def _get_api_key(self) -> str:
        """
        從 .env 檔案獲取 API 金鑰
        
        Returns:
            str: API 金鑰
        
        Raises:
            MissingAPIKeyError: 如果未找到有效的 API 金鑰
        """
        # 載入 .env 檔案
        load_dotenv()
        
        # 嘗試從環境變數獲取 API 金鑰
        api_key = os.getenv(self.app_id.upper() + '_API_KEY')

        if not api_key:
            raise MissingAPIKeyError(f"{self.app_id.upper()}_API_KEY")
        
        return api_key
    
    def set_system_prompt(self, system_prompt: str) -> None:
        """
        設定自訂系統提示詞
        
        Args:
            system_prompt (str): 新的系統提示詞
        """
        self.system_prompt = system_prompt
    
    def generate_block(self, 
             user_input: str, 
            ) -> str:
        """
        與 OpenAI API 進行對話
        
        Args:
            user_input (str): 使用者輸入
            model (str): 使用的模型，預設為 gpt-3.5-turbo
            temperature (float): 創造性參數 (0-2)，預設為 0.7
            max_tokens (Optional[int]): 最大回應長度
            conversation_history (Optional[List[Dict[str, str]]]): 對話歷史記錄
        
        Returns:
            str: AI 的回應
        """
        if not self.api_key:
            raise MissingAPIKeyError(f"OPENAI_API_KEY")
        
        model = "o4-mini"
        try:
            # 建立訊息列表
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # 添加當前使用者輸入
            messages.append({"role": "user", "content": user_input})
            
            # 調用 OpenAI API
            response = self.client.chat.completions.create(
                model=model,
                messages=messages
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"錯誤：無法獲取 AI 回應 - {str(e)}"
    
    def generate_and_save_block(self, user_input: str) -> str:
        """
        生成 block 並儲存到指定檔案
        
        Args:
            user_input (str): 使用者輸入
        
        Returns:
            str: 儲存的檔案名稱
        """
        block_code = self.generate_block(user_input)
        
        # 清理代碼塊，移除可能的 ``` 標記
        cleaned_code = self._clean_code_block(block_code)
        
        # 提取類名
        class_name = self._extract_class_name(cleaned_code)
        
        if class_name:
            # 將駝峰式命名轉換為蛇形命名
            snake_case_name = self._camel_to_snake(class_name)
            file_path = f"{snake_case_name}.py"
        else:
            raise RuntimeError("無法從生成的代碼中提取類名，請檢查生成的代碼是否正確。")
        
        # 儲存到檔案
        with open("./blocks/" + file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_code)
        
        return file_path
    
    def _clean_code_block(self, code: str) -> str:
        """
        清理代碼塊，移除可能的 ``` 標記和多餘的空白
        
        Args:
            code (str): 原始代碼
        
        Returns:
            str: 清理後的代碼
        """
        # 移除開頭和結尾的 ``` 標記
        cleaned = code.strip()
        
        # 移除開頭的 ```python 或 ```
        if cleaned.startswith('```python'):
            cleaned = cleaned[9:].lstrip('\n')
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:].lstrip('\n')
        
        # 移除結尾的 ```
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3].rstrip('\n')
        
        return cleaned.strip()
    
    def _extract_class_name(self, code: str) -> str:
        """
        從代碼中提取類名
        
        Args:
            code (str): Python 代碼
        
        Returns:
            str: 類名，如果找不到則返回空字串
        """
        # 使用正則表達式匹配 class 定義
        class_pattern = r'class\s+([A-Za-z_][A-Za-z0-9_]*)\s*[\(:]'
        match = re.search(class_pattern, code)
        
        if match:
            return match.group(1)
        return ""
    
    def _camel_to_snake(self, camel_str: str) -> str:
        """
        將駝峰式命名轉換為蛇形命名
        
        Args:
            camel_str (str): 駝峰式命名的字串
        
        Returns:
            str: 蛇形命名的字串
        """
        # 在大寫字母前插入底線（除了字串開頭）
        s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', camel_str)
        # 處理連續大寫字母的情況
        s2 = re.sub('([A-Z])([A-Z][a-z])', r'\1_\2', s1)
        # 轉換為小寫
        return s2.lower()


# 簡單使用範例
if __name__ == "__main__":
    try:
        load_dotenv()  # 載入 .env 檔案中的環境變數
        # 建立 OpenAI 客戶端實例
        client = BlockGenerator(os.getenv("COM.OPENAI_API_KEY"))
        
        # 簡單對話測試
        response = client.generate_and_save_block("幫助我生成一個能夠讓 discord 發送訊息到我的頻道的 block。")
        # print(f"AI 回應: {response}")
        print(response)
        
    except ValueError as e:
        print(f"設定錯誤: {e}")
    except Exception as e:
        print(f"執行錯誤: {e}")

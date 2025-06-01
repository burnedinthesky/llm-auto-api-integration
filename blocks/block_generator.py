import os
from typing import Dict, Any
from dotenv import load_dotenv
from openai import OpenAI


class BlockGenerator:
    """
    OpenAI API 客戶端類別，用於用使用者輸入產生 block
    """
    
    def __init__(self):
        """
        初始化 OpenAI 客戶端
        """

        self.app_id = "com.openai"
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
            "從 .env 檔案中，使用 app_id 讀取 API token 或其他必要的設定。"
            "在 init 方法中，讀取 API token及其他必要設定，如果有缺失，使用 input() 告訴使用者應該如何獲得需要的參數，"
            "並請使用者輸入，並且儲存到 .env 檔案中。"
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
        從 .env 檔案獲取 OpenAI API 金鑰
        
        Returns:
            str: OpenAI API 金鑰
        
        Raises:
            ValueError: 如果未找到有效的 API 金鑰
        """
        # 載入 .env 檔案
        load_dotenv()
        
        # 嘗試從環境變數獲取 API 金鑰
        api_key = os.getenv(self.app_id.upper() + '_API_KEY')
        
        if not api_key or api_key == 'your_openai_api_key_here':
            api_key = input(
                "未找到有效的 OpenAI API 金鑰。請在 .env 檔案中設定 OPENAI_API_KEY，"
                "或到 https://platform.openai.com/api-keys 獲取您的 API 金鑰，"
                "並輸入您的 API 金鑰: "
            )
            self._save_api_key(api_key)
        
        return api_key
    
    def _save_api_key(self, api_key: str) -> None:
        """
        儲存 API 金鑰到 .env 檔案
        
        Args:
            api_key (str): OpenAI API 金鑰
        """
        # 檢查 .env 檔案是否存在
        if not os.path.exists('.env'):
            with open('.env', 'w') as f:
                f.write(f"{self.app_id.upper()}_API_KEY={api_key}\n")
        else:
            # 檢查是否已經存在相同的 API 金鑰
            with open('.env', 'r') as f:
                lines = f.readlines()
            if any(line.startswith(f"{self.app_id.upper()}_API_KEY=") for line in lines):
                print("API 金鑰已存在於 .env 檔案中。")
                return
            else:
                with open('.env', 'a') as f:
                    f.write(f"{self.app_id.upper()}_API_KEY={api_key}\n")
                print("API 金鑰已儲存到 .env 檔案中。")
    
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
    
    def get_app_info(self) -> Dict[str, Any]:
        """
        取得應用程式資訊
        
        Returns:
            Dict[str, Any]: 包含應用程式 ID 和系統提示詞的字典
        """
        return {
            "app_id": self.app_id,
            "system_prompt": self.system_prompt,
            "model_available": True if self.api_key else False
        }


# 簡單使用範例
if __name__ == "__main__":
    try:
        # 建立 OpenAI 客戶端實例
        client = BlockGenerator()
        
        # 簡單對話測試
        response = client.generate_block("幫助我生成一個能夠讓 discord 發送訊息到我的頻道的 block。")
        # print(f"AI 回應: {response}")
        with open("block.py", "w") as f:
            f.write(response)
        
    except ValueError as e:
        print(f"設定錯誤: {e}")
    except Exception as e:
        print(f"執行錯誤: {e}")

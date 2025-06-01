# LLM Auto API Integration

An LLM-powered platform enabling users to effortlessly integrate and automate services across multiple APIs using a block-based interface.

## Installation

This project uses the [uv](https://docs.astral.sh/uv/) package manager, if you haven't installed uv, please refer to their [installation guidelines](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer).

After installing uv, simply run `uv sync` to create a virtual environment that has all required packages installed.

To start the app, run `uv run main.py`.

On first launch, you’ll be prompted in the terminal to enter your **OpenAI API key**.

## programming
### generate block
Use blocks/block_generator.py to generate a block. The parameter is a natural language string. For example
```python
print(BlockGenerator().generate_block("幫助我生成一個能夠讓 discord 發送訊息到我的頻道的 block。"))
```

# 安装说明

## 系统要求

### 1. Python依赖
```bash
pip install -r requirements.txt
```

### 2. Tesseract OCR (用于图片转文字功能) - 可选

**注意：** 图片转文字功能是可选的。如果没有安装Tesseract OCR，应用仍可正常运行，只是图片转文字功能会被禁用。

#### macOS
```bash
# 方法1：使用Homebrew（推荐）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install tesseract

# 方法2：直接下载安装包
# 从 https://github.com/UB-Mannheim/tesseract/wiki 下载macOS安装包
```

#### Ubuntu/Debian
```bash
sudo apt-get install tesseract-ocr
```

#### Windows
1. 下载Tesseract安装包：https://github.com/UB-Mannheim/tesseract/wiki
2. 安装后，将Tesseract路径添加到系统环境变量

### 3. 配置环境变量
创建 `.env` 文件并添加：
```
DASHSCOPE_API_KEY=your_api_key_here
```

## 运行应用
```bash
python app.py
```

访问 http://localhost:8000 使用应用。

## 功能说明

### 1. 图片转文字
- 点击"图片转文字"按钮
- 选择包含英文文字的图片
- 系统会自动提取文字并添加到作文内容中

### 2. 增强的语法反馈
- 提供具体的错误类型分析
- 包含错误上下文
- 详细的解释和建议

### 3. 写作统计
- 连词数量统计
- 词汇重复统计  
- 语法错误统计
- 可视化目标达成情况

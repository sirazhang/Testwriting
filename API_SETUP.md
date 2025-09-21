# API 配置说明

## 通义千问 API 配置

本系统使用阿里云通义千问API进行作文分析。请按照以下步骤配置：

### 1. 获取API密钥

1. 访问 [阿里云DashScope控制台](https://dashscope.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 开通通义千问服务
4. 创建API密钥

### 2. 配置API密钥

#### 方法一：环境变量（推荐）

```bash
export DASHSCOPE_API_KEY=your_api_key_here
```

#### 方法二：创建.env文件

在项目根目录创建`.env`文件：

```env
DASHSCOPE_API_KEY=your_api_key_here
SECRET_KEY=your-secret-key-here
```

#### 方法三：直接修改config.py

```python
class Config:
    DASHSCOPE_API_KEY = "your_api_key_here"
    SECRET_KEY = "your-secret-key-here"
    DEBUG = True
```

### 3. 验证配置

启动应用后，如果看到以下消息说明配置成功：

```
✅ DashScope API key configured successfully
```

如果看到警告消息，请检查API密钥配置。

### 4. 测试API连接

1. 启动应用：`python3 app.py`
2. 访问：http://localhost:8000
3. 输入作文内容并提交
4. 查看是否正常返回分析结果

### 5. 常见问题

**Q: 提示"No api key provided"**
A: 请确保已正确设置DASHSCOPE_API_KEY环境变量

**Q: 提示"API调用失败"**
A: 请检查API密钥是否有效，账户是否有足够余额

**Q: 分析结果不准确**
A: 可以调整prompt模板或尝试不同的模型参数

### 6. 费用说明

- 通义千问按调用次数计费
- 建议先使用少量测试
- 可在DashScope控制台查看使用量和费用

### 7. 备用方案

如果无法使用通义千问API，系统会自动使用fallback模式，提供基础的评分和反馈。

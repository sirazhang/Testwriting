# 故障排除指南

## "Fail to fetch" 错误解决方案

### 1. 检查服务器状态
确保Flask应用程序正在运行：
```bash
# 在项目目录中运行
python3 app.py
```

您应该看到类似输出：
```
* Serving Flask app 'app'
* Debug mode: on
* Running on http://127.0.0.1:8000
```

### 2. 检查端口
确保端口8000没有被其他程序占用：
```bash
lsof -i :8000
```

如果端口被占用，可以修改`app.py`文件中的端口号：
```python
app.run(debug=True, port=8001)  # 改为其他端口
```

### 3. 检查网络连接
在浏览器中直接访问：http://127.0.0.1:8000

如果无法访问，请检查：
- 防火墙设置
- 网络连接
- 浏览器是否阻止了本地连接

### 4. 浏览器开发者工具
按F12打开开发者工具，查看：
- **Console标签**：查看JavaScript错误
- **Network标签**：查看网络请求状态
- **Application标签**：检查本地存储

### 5. 常见错误及解决方案

#### 错误：CORS policy
**解决方案**：已在代码中配置CORS，如果仍有问题，请清除浏览器缓存。

#### 错误：Connection refused
**解决方案**：
1. 确认服务器正在运行
2. 检查端口是否正确
3. 重启应用程序

#### 错误：Google API错误
**解决方案**：
1. 检查API密钥是否正确
2. 确认网络可以访问Google服务
3. 检查API配额是否用完

### 6. 测试连接
使用提供的测试页面：
1. 访问：http://127.0.0.1:8000/test_connection.html
2. 点击"测试连接"按钮
3. 查看测试结果

### 7. 手动测试API
使用curl命令测试：
```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"topic": "Test", "essay": "This is a test."}'
```

### 8. 重置应用程序
如果问题持续存在：
1. 停止应用程序（Ctrl+C）
2. 清除浏览器缓存
3. 重新启动应用程序
4. 刷新浏览器页面

### 9. 检查依赖
确保所有依赖已安装：
```bash
pip3 install -r requirements.txt
```

### 10. 日志检查
查看Flask应用程序的控制台输出，寻找错误信息。

## 联系支持
如果问题仍未解决，请提供：
1. 浏览器控制台的错误信息
2. Flask应用程序的控制台输出
3. 操作系统信息
4. 浏览器版本信息

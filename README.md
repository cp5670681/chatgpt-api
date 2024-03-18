# 爬取chatgpt页面的api
## 安装
### 虚拟环境
新建虚拟环境
```
python -m venv venv
```
进入虚拟环境  
linux:
```
source venv/bin/activate
```
windows:  
```
venv\Scripts\activate
```
### 安装依赖
```
pip install -r requirements.txt
```
### 配置
复制.env.sample到.env  
填入从 https://chat.openai.com/ 页面的接口中获取请求头中的 "authorization"
## 使用示例
```python
gpt = ChatgptApi(os.getenv('AUTHORIZATION'))
gpt.chat('question')
```

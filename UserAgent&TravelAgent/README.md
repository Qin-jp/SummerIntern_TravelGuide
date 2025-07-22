## 环境安装
> 按照Qwen-Agent库中的README安装指定的包即可。  
我这里使用python=3.11.13，nodejs=20.17.0，在用conda命令创建环境的时候指定版本就行。
> 运行代码的时候将Qwen-Agent文件夹和UserAgnet&TravelAgent文件夹并列放置即可。

## 关键代码说明

### UserAgent
> UserAgent.py实现了拆分约束和根据多轮对话实现问题$x_n$的过程。

### TravelAgent
> TravelAgent.py利用QwenAgent实现了KB加持下的$y_n$旅游攻略生成的过程。

### Demo
> Demo.py实现了4轮交互对话生成攻略，同时生成的一些记录输出的文件在同一文件夹下。

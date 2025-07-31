## 旅行规划数据集的生成

### code
> code文件夹中包含DatasetGenerator、UserAgent&TravelAgent文件夹 <br>
>> DatasetGenerator中包含原始数据生成的代码 <br>
>> UserAgent&TravelAgent中包含用户智能体、旅游规划智能体以及一个多轮对话的Demo

### TravelGuideDataSet
> 其中包含训练集、测试集、验证集，具体信息如下：<br>
>> train：280个城市 一共12305对攻略+约束<br>
> test： 35 个城市 一共1551对攻略+约束<br>
> val：  35 个城市 一共1656对攻略+约束<br>

### process_data与final_data
> 其中包含原始数据生成过程中的过渡形态的数据（html、txt、md格式的攻略）

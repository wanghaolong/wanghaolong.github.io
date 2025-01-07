
# PlantUML 经验分享

## 1. 简单介绍 PlantUML

**PlantUML** 是一种基于文本描述的图表生成工具，支持多种 UML 图表类型，包括时序图、类图、活动图和组件图等。它通过简单的代码描述生成专业的图表，尤其适合程序员在软件设计和文档编写中使用。

### **PlantUML 的主要特点**
- **简单高效**：使用纯文本语法描述图表，省去了手动绘图的繁琐步骤。
- **易于版本管理**：基于文本格式，方便在版本控制工具中进行追踪和协作。
- **强大的集成能力**：支持多种 IDE（如 IntelliJ IDEA）和工具（如 VS Code）。
- **支持多种图表类型**：时序图、类图、活动图、组件图等多种 UML 图表类型。

---

## 2. 快速体验

### 2.1 在线体验
搜索引擎搜索 **PlantUML 在线工具**，可以找到很多在线工具，例如 [PlantText](https://www.planttext.com/)。
输入以下示例代码，即可生成时序图:
   ```plantuml
   @startuml
   Alice -> Bob: Hello
   Bob -> Alice: Hi
   @enduml
   ```



### 2.2 在IntelliJ IDEA中使用 PlantUML（MacOS环境）

#### 步骤 1：安装Graphviz
   1. 使用 Homebrew 安装 **Graphviz**：
   ```bash
   brew install graphviz
   ```
   2. 执行如下命令，如果安装成功，将显示版本号。
   ```bash
   dot -version
   ```
 
   3. 执行如下命令， 记住安装路径，例如：`/opt/homebrew/bin/dot`。
   ```bash
   which dot
   ```

#### 步骤 2：下载 **PlantUML JAR 文件**：

   1. 前往 [PlantUML 下载页面](https://plantuml.com/download)。
   2. 下载 `plantuml.jar` 文件并保存到固定目录，例如：`~/tools/plantuml.jar`。

#### 步骤 3：在IntelliJ IDEA中，安装 PlantUML 插件
1. 打开 IntelliJ IDEA。
2. 进入 **File > Settings > Plugins**。
3. 搜索 **PlantUML Integration**，点击 **Install** 安装插件。
4. 安装完成后，重启 IDEA。

#### 步骤 4：在IntelliJ IDEA中，配置 PlantUML 插件
![alt text](image.png)


#### 步骤 5：在IntelliJ IDEA中，创建并运行 PlantUML 文件
1. 在项目中创建一个 `.puml` 文件，例如：`example.puml`。
2. 输入以下代码：
   ```plantuml
   @startuml
   Alice -> Bob: Hello
   Bob -> Alice: Hi
   @enduml
   ```
3. 右边会显示生成的图表。

---

## 3. 使用案例介绍

### 3.1 时序图

#### 3.1.1 多系统对接时，通过plantUML快速生成时序图，提高沟通效率
![alt text](image-3.png)
具体代码如下：
```plantuml
@startuml
entity 志合东方APP as app
entity 中考前端
entity 中考后端
entity 用户中心 as u2
app -> app: APP登录
app -> 中考前端: 打开H5页面(携带sid)
group 模拟u2登录
中考前端 -> 中考后端: 模拟u2登录(携带sid)
activate 中考后端
中考后端 -> app: 验证sid，获取u2userId
中考后端 -> u2 : 根据u2userId获取u2at
中考后端 -> 中考后端: 保存costomer记录
中考后端 -> 中考前端: 返回u2at
deactivate 中考后端
end group
@enduml
```
#### 3.1.2 梳理现有系统的调用关系，通过plantUML生成时序图，方便理解


---

### 3.2 活动图
活动图描述动态流程。以下是一个简单的活动图代码：
```plantuml
@startuml
start
:Input Credentials;
if (Valid Credentials?) then (yes)
  :Grant Access;
else (no)
  :Deny Access;
endif
stop
@enduml
```

---

### 3.3 类图
类图展示类及其之间的关系。以下是一个简单的类图代码：
```plantuml
@startuml
class User {
  +String name
  +String email
  +login()
}
class Admin {
  +manageUsers()
}
User <|-- Admin
@enduml
```

---

### 3.4 组件图
组件图展示系统中的组件及其相互依赖关系。以下是一个组件图的示例代码：
```plantuml
@startuml
package "Web Application" {
  [Frontend] --> [Backend]
  [Backend] --> [Database]
}
@enduml
```

---

## 4. 与 AI 工具的结合

### 4.1 GitHub Copilot 
结合 **GitHub Copilot**，可以更快地生成 PlantUML 代码，以下是一个真实工作场景，用于生成[中考志愿技术文档](https://alidocs.dingtalk.com/i/nodes/AR4GpnMqJzMLzPPoio049KR9VKe0xjE3?iframeQuery=utm_source%3Dportal%26utm_medium%3Dportal_recent&rnd=0.2049844496574701)中的权限判断流程图。
首选在idea中打开copilot，如下图所示：
![alt text](image-2.png)
- **首次请求**，生成的plantUML代码如下：

```plantuml
@startuml
start
:Retrieve email from LoginUserThreadLocal;
:Retrieve DataPermissionDO by email;
if (permissionDB == null) then (yes)
    :Return false;
    stop
else (no)
    :Retrieve DataPermissionTypeEnum from permissionDB;
    if (typeEnum == DataPermissionTypeEnum.ALL) then (yes)
        :Return true;
        stop
    else (no)
        :Retrieve DataPermissionDetailsDO list by permissionDB id;
        if (details is empty) then (yes)
            :Return false;
            stop
        else (no)
            :Group details by schoolId;
            :Retrieve current school details from grouped details;
            if (curSchoolDetails is empty) then (yes)
                :Return false;
                stop
            else (no)
                if (typeEnum == DataPermissionTypeEnum.SCHOOL) then (yes)
                    :Return true;
                    stop
                else (no)
                    :Iterate over curSchoolDetails;
                    if (detail.deptCode equals deptCode) then (yes)
                        :Return true;
                        stop
                    else (no)
                        :Continue iteration;
                    endif
                    :Return false;
                    stop
                endif
            endif
        endif
    endif
endif
@enduml
```
- **"要求中文输出"**，再次请求，生成的代码如下：
```plantuml
@startuml
start
:从 LoginUserThreadLocal 获取邮箱;
:根据邮箱查询 DataPermissionDO;
if (permissionDB == null) then (是)
    :返回 "没有部门权限";
    stop
else (否)
    :获取 permissionDB 的 DataPermissionTypeEnum;
    if (typeEnum == DataPermissionTypeEnum.ALL) then (是)
        :返回 "有部门权限";
        stop
    else (否)
        :根据 permissionDB id 查询 DataPermissionDetailsDO 列表;
        if (details 为空) then (是)
            :返回 "没有部门权限";
            stop
        else (否)
            :按 schoolId 分组 details;
            :从分组中获取当前学校的权限明细;
            if (curSchoolDetails 为空) then (是)
                :返回 "没有部门权限";
                stop
            else (否)
                if (typeEnum == DataPermissionTypeEnum.SCHOOL) then (是)
                    :返回 "有部门权限";
                    stop
                else (否)
                    :遍历 curSchoolDetails;
                    if (detail.deptCode 等于 deptCode) then (是)
                        :返回 "有部门权限";
                        stop
                    else (否)
                        :继续遍历;
                    endif
                    :返回 "没有部门权限";
                    stop
                endif
            endif
        endif
    endif
endif
@enduml
```
- **"假设这个图是给非程序员看的，在不改变业务逻辑的前提下，简化一下"**，再次请求，生成的代码如下：
```plantuml
@startuml
start
:获取当前用户的邮箱;
:根据邮箱查询权限记录;
if (没有权限记录) then (是)
    :返回 "没有部门权限";
    stop
else (否)
    :获取权限类型;
    if (权限类型是全部) then (是)
        :返回 "有部门权限";
        stop
    else (否)
        :查询权限明细;
        if (没有权限明细) then (是)
            :返回 "没有部门权限";
            stop
        else (否)
            :按学校分组权限明细;
            :获取当前学校的权限明细;
            if (没有当前学校的权限) then (是)
                :返回 "没有部门权限";
                stop
            else (否)
                if (权限类型是学校) then (是)
                    :返回 "有部门权限";
                    stop
                else (否)
                    :遍历当前学校的权限明细;
                    if (找到匹配的部门) then (是)
                        :返回 "有部门权限";
                        stop
                    else (否)
                        :继续遍历;
                    endif
                    :返回 "没有部门权限";
                    stop
                endif
            endif
        endif
    endif
endif
@enduml
```
- **"使用不同配色突出返回有权限和无权限的节点，要求配色优雅简洁"**，再次请求，生成的代码如下：
```plantuml
@startuml
skinparam backgroundColor #F5F5F5
skinparam activity {
    BackgroundColor #FFFFFF
    BorderColor #B0B0B0
    StartColor #87CEEB
    EndColor #FF6347
    DiamondBackgroundColor #F0E68C
    DiamondBorderColor #B0B0B0
    ArrowColor #4682B4
}

start
:获取当前用户的邮箱;
:根据邮箱查询权限记录;
if (没有权限记录) then (是)
    :<color:red>返回 "没有部门权限"</color>;
    stop
else (否)
    :获取权限类型;
    if (权限类型是全部) then (是)
        :<color:green>返回 "有部门权限"</color>;
        stop
    else (否)
        :查询权限明细;
        if (没有权限明细) then (是)
            :<color:red>返回 "没有部门权限"</color>;
            stop
        else (否)
            :按学校分组权限明细;
            :获取当前学校的权限明细;
            if (没有当前学校的权限) then (是)
                :<color:red>返回 "没有部门权限"</color>;
                stop
            else (否)
                if (权限类型是学校) then (是)
                    :<color:green>返回 "有部门权限"</color>;
                    stop
                else (否)
                    :遍历当前学校的权限明细;
                    if (找到匹配的部门) then (是)
                        :<color:green>返回 "有部门权限"</color>;
                        stop
                    else (否)
                        :继续遍历;
                    endif
                    :<color:red>返回 "没有部门权限"</color>;
                    stop
                endif
            endif
        endif
    endif
endif
@enduml
```

---
### 4.2 Windsurf
结合 **Windsurf**，快速生成业务流程图，以下是一个真实工作场景，用于生成[主管消息优化](https://alidocs.dingtalk.com/i/nodes/amweZ92PV6vZR33dfEQe2aBlVxEKBD6p)中的业务流程变更图。

- 首先让我们看看代码改了啥
    - 新增通用C端消息发送逻辑
![alt text](image-4.png)
    - 移除线索创建职责链中的主管消息发送逻辑
![alt text](image-5.png)

- 先让copilot总结变更（有点挫，无法使用）
  ![alt text](image-6.png)

- 再让windsurf总结变更
![alt text](image-9.png)
![alt text](image-10.png)
![alt text](image-11.png)
![alt text](image-12.png)
- windsurf生成的代码如下：
```plantuml
@startuml
skinparam backgroundColor white
skinparam activity {
    BorderColor black
    BackgroundColor white
    ArrowColor black
}

|ActivityDetailChainService|
start
:处理活动详情;
if (是否为基础详情处理) then (yes)
  :BaseDetailSaveHandler;
  :BaseDetailClueHandler;
  :BaseDetailNoticeHandler;
  
  |#Pink|ClueEventService|
  :<font color=red>新增: commonEventChainHandle处理</font>;
endif

|ClueCreateCmdHandler|
:按策略生成或关联线索;
fork
  :<font color=red>删除: sendWaitHandOverToManagerIfNeed</font>;
fork again
  :afterRelateOpp处理;
end fork

stop
@enduml

```
- 然后我发现代码漏了一个流程，于是修改代码
![alt text](image-13.png)
![alt text](image-14.png)
- 再次让windsurf总结变更
  ![alt text](image-15.png)
  ![alt text](image-16.png)

- 生成代码如下：
```plantuml
@startuml
skinparam backgroundColor white
skinparam activity {
    BorderColor black
    BackgroundColor white
    ArrowColor black
}

|#LightGray|旧流程|
partition "原有流程" {
    start
    :ActivityDetailChainService处理活动详情;
    :BaseDetailSaveHandler;
    :BaseDetailClueHandler;
    fork
        :ClueCreateCmdHandler处理;
        :生成或关联线索;
        :#pink:直接发送等待分配给主管的消息;
        note right: 原逻辑在ClueCreateCmdHandler中直接发送
    fork again
        :BaseDetailNoticeHandler;
    end fork
    :结束处理;
    stop
}

|#LightBlue|新流程|
partition "重构后流程" {
    start
    :ActivityDetailChainService处理活动详情;
    :BaseDetailSaveHandler;
    :BaseDetailClueHandler;
    fork
        :ClueCreateCmdHandler处理;
        :生成或关联线索;
        note right: 移除了直接发送消息的逻辑
    fork again
        :BaseDetailNoticeHandler;
    end fork
    
    :#pink:ClueEventService.commonEventChainHandle;
    note right
    新增事件处理服务
    统一处理消息发送逻辑
    end note
    
    :结束处理;
    stop
}

legend right
    |颜色|说明|
    |#pink|变更部分|
    |#LightGray|原有流程|
    |#LightBlue|新流程|
endlegend

@enduml

```
- 依然不太满意，自己画旧版逻，让windSurf生成新版逻辑
旧版逻辑如下：
```plantuml
@startuml
skinparam backgroundColor white
:系统对接或批量导入线索;
partition "线索创建职责链" {


group 线索创建
:线索初始化;
if(未命中分配策略且状态为待交接?) then (yes)
    :给创建部门主管发待交接消息;
    note right: 即使转商了，也会发线索消息
endif
end group


group 线索转商
if(命中转商策略?) then (yes)
    :线索转商;
endif
end group
group 关联任务
if(命中分配策略?) then (yes)
    :分配线索;
    :给主管发待分配消息;
    note right: 即使转商了，也会发线索消息
endif
end group
@enduml

```
- windsurf生成的新版逻辑如下：
![alt text](image-20.png)
```plantuml
@startuml
|线索创建职责链|
start
:系统对接或批量导入线索;

group 线索创建
    :线索初始化;
    note right: 不再在此处发送消息
end group

group 关联任务
    if (命中分配策略?) then (yes)
        :分配线索;
        note right: 不再在此处发送消息
    endif
end group

|事件处理服务|
:获取线索信息;

if (是否已转商机?) then (yes)
    #pink:不发送消息;
    note right: 已转商机的线索不需要发送消息
else (no)
    if (线索状态?) then (待分配)
        #pink:给主管发待分配消息;
        note right
            命中策略且分配到部门时
            调用sendHandOverToManager
            传入部门ID和策略名称
        end note
    else (待交接)
        #pink:给创建部门主管发待交接消息;
        note right
            调用sendWaitHandOverToManager
            传入创建部门ID
        end note
    endif
endif

note right
    异常处理：
    所有异常都会被捕获并记录
    不影响主流程继续执行
end note

stop
@enduml
```
- 再次细化
![alt text](image-21.png)

```plantuml
@startuml
|线索创建职责链|
start
:系统对接或批量导入线索;

group 线索创建
    :线索初始化;
    note right: 不再在此处发送消息
end group

group 关联任务
    if (命中分配策略?) then (yes)
        :分配线索;
        note right: 不再在此处发送消息
    endif
end group

|事件处理服务|
:获取线索信息;

if (是否已转商机?) then (yes)
    #pink:不发送消息;
    note right: 已转商机的线索不需要发送消息
else (no)
    if (线索状态?) then (待分配)
        #pink:给主管发待分配消息;
        note right
            命中策略且分配到部门时
            调用sendHandOverToManager
            传入部门ID和策略名称
        end note
    else (待交接)
        #pink:给创建部门主管发待交接消息;
        note right
            调用sendWaitHandOverToManager
            传入创建部门ID
        end note
    endif
endif

note right
    异常处理：
    所有异常都会被捕获并记录
    不影响主流程继续执行
end note

stop
@enduml
```

  



  

## 5. 总结优势




**PlantUML 的主要优势**：
1. **高效**：通过简单的文本描述快速生成图表，节省时间。
2. **灵活**：支持多种 UML 图表，满足多种设计需求。
3. **易集成**：可以集成到各种 IDE 和工具中。
4. **版本管理友好**：基于文本格式，方便协作和版本控制。
5. **结合 AI 提升效率**：与 ChatGPT 和 Copilot 配合使用，可以快速生成所需的图表代码。

PlantUML 是一个强大且灵活的工具，非常适合程序员在设计、开发和文档编写中使用！


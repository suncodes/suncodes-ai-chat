# Poetry 基本用法

‍

常用命令

|功能|命令|
| -----------------------------| --------------------------------------------------------------------------------------|
|创建项目|poetry new <project\_name><br />常用参数：--src：使用 src 包结构<br />|
|添加依赖|poetry add <package>|
|添加开发依赖|poetry add --dev <package>|
|移除依赖|poetry remove <package>|
|安装依赖|poetry install|
|更新依赖|poetry update|
|管理虚拟环境|poetry env info<br />poetry env use<br />poetry env list<br />poetry env remove<br />|
|激活(创建)虚拟环境|poetry shell|
|退出虚拟环境|exit|
|在虚拟环境中运行|poetry run <command>|
|打包项目|poetry build|
|发布到 PyPI|poetry publish|
|查看依赖树|poetry show --tree|
|检查配置是否正确|poetry check|

‍

## 安装 poetry

```text
pip install poetry
```

安装的位置：${python安装目录}/Scripts/poetry.exe

‍

### **配置变量（可选）**

熟悉配置命令：

```text
# 查看配置命令怎么用
poetry config --help


# 查看默认安装时配置了哪些东西
poetry config --list

cache-dir = "C:\\Users\\Administrator\\AppData\\Local\\pypoetry\\Cache"
experimental.system-git-client = false
installer.max-workers = null
installer.modern-installation = true
installer.no-binary = null
installer.parallel = true
keyring.enabled = true
solver.lazy-wheel = true
virtualenvs.create = true
virtualenvs.in-project = null
virtualenvs.options.always-copy = false
virtualenvs.options.no-pip = false
virtualenvs.options.no-setuptools = false
virtualenvs.options.system-site-packages = false
virtualenvs.path = "{cache-dir}\\virtualenvs"  # C:\Users\Administrator\AppData\Local\pypoetry\Cache\virtualenvs
virtualenvs.prefer-active-python = false
virtualenvs.prompt = "{project_name}-py{python_version}"
warnings.export = true
```

由于把缓存以及虚拟环境的路径默认放在了C盘，为了减少C盘的占用，改为D盘。

‍

配置 cache-dir：

```text
poetry config cache-dir "D:\\software\\install\\poetry-cache\\Cache"
```

验证是否配置正确：

```text
# 1.查看配置是否改变
poetry config --list

# 激活虚拟环境（不存在，则同时会创建）
# 必须在有 pyproject.toml 文件的目录下运行
poetry shell

# 之后去设置的目录下，看看有没有新建的虚拟环境文件即可。
D:\software\install\poetry-cache\Cache\virtualenvs\xxt-ai-chat-yycY1xCE-py3.12

# 删除创建的虚拟环境
poetry env remove xxt-ai-chat-yycY1xCE-py3.12
```

‍

‍

## 使用 poetry 管理项目流程

普通项目和 poetry管理的项目就差一个 `pyproject.toml`​ 的区别！！！

### 1. 创建项目或初始化已有项目

创建新项目

```text
poetry new my_project
```

如果已有项目，则可以初始化已有项目

```text
poetry init
```

它会生成并配置 `pyproject.toml`​ 文件，帮助你定义项目的元信息和依赖，而无需手动编辑配置文件。

运行命令后，`Poetry`​ 会进入交互式问答模式，帮助你完成配置：

```plaintext
This command will guide you through creating your pyproject.toml config.

Package name [my_project]: my_project
Version [0.1.0]: 1.0.0
Description []: A demo project for Poetry
Author [Your Name <you@example.com>, n to skip]: John Doe <john.doe@example.com>
License []: MIT
Compatible Python versions [^3.9]: ^3.8

Would you like to define your dependencies (require) interactively? (yes/no) [yes]: yes
```

‍

### 2. 激活虚拟环境（可忽略）

Poetry 的一个核心功能就是**自动管理虚拟环境**，让开发者无需手动操作。

* 如果未激活虚拟环境，`poetry add`​ 会直接在项目的虚拟环境中安装依赖。
* 如果虚拟环境已经激活，`poetry add`​ 会在当前虚拟环境中安装依赖。

‍

以下操作会自动创建虚拟环境：

```text
poetry add
poetry install
poetry update
poetry run
```

通常不需要手动创建、激活虚拟环境

‍

手动激活虚拟环境：

```text
poetry shell
```

‍

‍

### 3. 管理依赖

方式一：命令行方式执行命令，会自动更改 `pyproject.toml`​文件

* 添加依赖：

  ```bash
  poetry add <package>
  poetry add requests@^2.26.0  # 指定版本范围
  ```
* 添加开发依赖：

  ```bash
  poetry add --dev pytest
  ```
* 移除依赖：

  ```bash
  poetry remove <package>
  ```
* 查看依赖树：

  ```bash
  poetry show --tree
  ```

‍

方式二：直接在`pyproject.toml`​文件中，添加需要的依赖

* 修改`pyproject.toml`​文件

  ```text
  [tool.poetry.dependencies]
  python = "^3.12"
  requests = "^2.26.0"
  ```

* 安装依赖

  ```text
  poetry install
  或者 更新依赖（如果是更换依赖版本）
  poetry update
  ```

‍

|特性|poetry install|poetry update|
| ------------------| ----------------------------------| ----------------------------------|
|依据的文件|主要依赖 `poetry.lock`​ 文件|忽略 `poetry.lock`​，依据 `pyproject.toml`​|
|是否更新依赖版本|否，安装锁定版本|是，安装最新兼容版本并更新锁文件|
|是否修改`poetry.lock`​|不修改（如果不存在会新建）|会重新生成并覆盖|
|使用场景|新环境安装依赖，保持依赖版本一致|更新依赖到最新版本|

‍

### 4. 开发项目

跟之前一样

‍

### 5. 运行项目

```text
poetry run python script.py
```

‍

## 使用 Pycharm 运行 poetry 项目

### 1. 创建项目

```text
poetry new --src xxt-ai-chat
```

--src 参数：创建 src 类型的项目结构

‍

### 2. 使用 Pycharm 打开项目

File ---> Open --> 选择新创建的项目即可。

‍

### 3. 配置Python Interpreter

Pycharm 打开Python项目，默认会直接使用本机安装的Python。

如果检测到使用了 pyproject.toml 文件，则认为需要加载 Poetry 环境。

在软件右下角，会显示使用的什么 Python Interpreter。

如果没有自动加载Poetry 环境，则需要手动配置。

File ---> settings --->Project:xxx ---> Python Interpreter ---> Add Interpreter ---> Add Local Interpreter.

选择 Poetry Environment：

​![image](assets/image-20241220103907-801gjhk.png)​

‍

在 Poetry executable 中，添加之前安装 poetry 的安装目录。${python install dir}/Scripts/poetry.exe

```text
D:\software\install\Python\Python312\Scripts\poetry.exe
```

‍

### 4. 运行项目

在 项目中新建 a.py 文件

```text
print("Hello World")
```

直接运行 a.py 就可以了。

‍

‍

## 常用 pyproject.toml 配置

### [tool.poetry]：元信息

* **packages**

在 `pyproject.toml`​ 的 `[tool.poetry]`​ 部分中，`packages`​ 是一个可选字段，用于显式指定哪些目录或模块应该包含在打包过程中。通常，Poetry 会根据项目结构自动检测包，但通过 `packages`​ 字段可以对打包行为进行更精细的控制。

```text
[tool.poetry]
name = "my_project"
version = "1.0.0"
description = "A demo project"
authors = ["Your Name <email@example.com>"]

packages = [
    { include = "my_package" },
    { include = "another_package.submodule", from = "src" }
]

```

**字段说明**

* ​**​`include`​**​ **:**

  * 指定要包含的包的名称或路径。
  * 必须是顶级模块名或目录名。
* ​**​`from`​**​ **:**

  * 指定包的相对路径。如果包位于非默认路径（如 `src/`​），需要使用 `from`​ 明确指定。
  * 默认情况下，Poetry 会认为包在项目的根目录下。

‍

‍

[tool.poetry.dependencies]：项目依赖

[tool.poetry.dev-dependencies]：项目本地开发依赖

[build-system]：构建系统需要的参数，固定写法

‍

 **[tool.poetry.scripts]：自定义脚本，运行时可使用。**

```text
[tool.poetry.scripts]
command_name = "module.path:function_name"
```

**参数说明**

* ​**​`command_name`​**​：终端中运行的命令名称。
* ​**​`module.path`​**​：Python 模块的路径，使用点号分隔（如 `my_project.module`​）。
* ​**​`function_name`​**​：要调用的 Python 函数的名称。

‍

 **[tool.poetry.plugins]：自定义插件。**

‍

‍

‍

‍

‍

‍

‍

‍

‍

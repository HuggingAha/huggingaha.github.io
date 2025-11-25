---
title: "Linux常用指令"
showAuthor: false
date: 2022-07-16
description: "正则表达式（Regex）用法"
slug: "linux-operation"
tags: ["杂记", "linux 指令"]
# series: [""]
# series_order: 1
draft: false
---


无论是后端开发者、数据科学家，还是运维工程师，Linux 都是绕不开的强大工具。它稳定、高效、开源，是现代服务器和开发环境的基石。掌握常用的 Linux 命令，能极大地提升工作效率。

本文内容涵盖文件操作、进程监控、远程会话管理等核心领域。

### 1. Linux 命令的基本哲学

在开始之前，先了解 Linux 命令的基本格式和两个核心哲学。

**命令格式:**

```bash
command [options] [arguments]
```

- `command`: 你要执行的命令，如 `ls`, `cd`。
- `options`: 命令的选项或标志，通常以  (短选项，如 `l`) 或 `-` (长选项，如 `-all`) 开头，用于调整命令的行为。
- `arguments`: 命令作用的对象，通常是文件名或路径。

**核心哲学:**

1. **一切皆文件 (Everything is a file)**：在 Linux 中，硬件设备、目录、网络连接等都被抽象为文件，这使得我们可以用统一的方式来处理它们。
2. **组合小程序，完成复杂任务**：Linux 提倡使用功能单一的小工具，通过管道（Pipe）将它们组合起来，像乐高积木一样搭建出强大的功能。

### 2. 文件与目录核心操作

这是最基础也是最频繁的操作。

| 命令 | 描述 | 常用示例 |
| --- | --- | --- |
| `ls` | 列出目录中的文件和子目录。 | `ls -alh` (列出所有文件，包括隐藏文件，并以人类可读的格式显示大小) |
| `cd` | 切换当前工作目录。 | `cd /var/log` (切换到指定目录) <br> `cd ..` (返回上一级目录) <br> `cd ~` 或 `cd` (返回家目录) |
| `pwd` | 显示当前所在的目录路径。 | `pwd` |
| `mkdir` | 创建新目录。 | `mkdir my_project` <br> `mkdir -p dir1/dir2` (-p 选项可以递归创建多层目录) |
| `touch` | 创建一个空文件或更新文件时间戳。 | `touch new_file.txt` |
| `cp` | 复制文件或目录。 | `cp source.txt dest.txt` <br> `cp -r source_dir/ dest_dir/` (-r 选项用于递归复制整个目录) |
| `mv` | 移动或重命名文件/目录。 | `mv old_name.txt new_name.txt` (重命名) <br> `mv file.txt /path/to/dest/` (移动) |
| `rm` | 删除文件或目录。 | `rm file.txt` <br> `rm -r old_dir/` (-r 选项用于递归删除目录) <br> **警告：`rm -rf /` 是世界上最危险的命令，请谨慎使用 `-rf`！** |
| `chmod` | 修改文件或目录的权限。 | `chmod u+x script.sh` (给文件的所有者 `u` 增加可执行权限 `x`) <br> `chmod 755 script.sh` (使用数字模式设置权限) |

### 3. IO 重定向与管道

这是发挥 Linux "组合" 哲学威力的关键。

- **管道 `|`**
将上一个命令的**标准输出 (stdout)** 连接到下一个命令的**标准输入 (stdin)**。
**示例**：查找所有 Python 相关的进程。
    
    ```bash
    ps -aux | grep python
    ```
    
- **重定向 `>` 和 `>>`**
将命令的输出重定向到文件，而不是显示在屏幕上。
    - `>` (覆盖)：如果文件存在，则覆盖其内容；如果不存在，则创建新文件。
    - `>>` (追加)：如果文件存在，则将输出追加到文件末尾；如果不存在，则创建新文件。
    
    **示例**：
    
    ```bash
    # 将命令输出保存到 log.txt (覆盖)
    ls -l > log.txt
    
    # 将新的日志追加到 log.txt
    echo "This is a new log entry" >> log.txt
    ```
    
- **标准输出与标准错误**
Linux 中有两个主要的输出流：
    - `1`: 标准输出 (stdout)
    - `2`: 标准错误 (stderr)
    默认情况下，`>` 只重定向标准输出。要同时重定向两者，可以使用 `2>&1`。
    **示例**：将命令的所有输出（包括错误信息）都保存到文件。
    
    ```bash
    ./my_program > output.log 2>&1
    ```
    

### 4. 进程监控与管理

实时了解系统正在运行什么，并对它们进行管理。

- **`ps -aux`**
静态查看当前系统的所有进程。
    - `USER`: 进程所有者
    - `PID`: 进程 ID，是进程的唯一标识。
    - `%CPU`: CPU 使用率。
    - `%MEM`: 内存使用率。
    - `STAT`: 进程状态 (R:运行, S:睡眠, Z:僵尸)。
    - `COMMAND`: 启动进程的命令。
- **`top`**
动态、实时地显示系统进程状态，相当于任务管理器。
    - `PID`, `USER`, `%CPU`, `%MEM`, `COMMAND`: 与 `ps` 类似。
    - `PR`: 优先级。
    - `NI`: Nice 值，负值表示高优先级。
    - 在 `top` 界面，可以按 `P` (按CPU排序)，`M` (按内存排序)，`q` (退出)。
- **`kill`**
向进程发送信号，通常用于终止进程。
    
    ```bash
    # 优雅地终止进程 (发送 SIGTERM 信号)
    kill [PID]
    
    # 强制终止进程 (发送 SIGKILL 信号)，用于进程无响应时
    kill -9 [PID]
    ```
    

### 5. GPU 资源监控 (AI/ML 必备)

对于进行深度学习等计算密集型任务的用户，`nvidia-smi` 是必不可少的工具。

- **`nvidia-smi`**
实时监控 NVIDIA GPU 的状态。
    - `Fan`: 风扇转速。
    - `Temp`: GPU 温度。
    - `Perf`: 性能状态 (P0 最高，P12 最低)。
    - `Pwr:Usage/Cap`: 当前功耗 / 总功耗。
    - `Memory-Usage`: **显存使用量**，这是最常关注的指标。
    - `GPU-Util`: GPU 利用率。
    - 下方会列出当前正在使用 GPU 的进程及其 PID 和显存占用。
- **指定使用的 GPU**
当服务器有多张 GPU 时，可以通过环境变量 `CUDA_VISIBLE_DEVICES` 来指定程序在哪张卡上运行。
**命令行中指定**：
    
    ```bash
    # 让 python 程序只在 GPU 1 上运行
    CUDA_VISIBLE_DEVICES=1 python my_script.py
    ```
    
    **在 Python 脚本中指定**：
    
    ```python
    import os
    os.environ["CUDA_VISIBLE_DEVICES"] = "0" # 指定使用 GPU 0
    # 后续的 PyTorch 或 TensorFlow 代码将只会看到 GPU 0
    ```
    

### 6. 文本编辑神器：Vim

Vim 是 Linux 环境下强大的文本编辑器，虽然学习曲线陡峭，但回报巨大。

- **三种模式**
    1. **正常模式 (Normal Mode)**: 默认模式，用于移动光标、删除、复制、粘贴文本。
    2. **插入模式 (Insert Mode)**: 用于输入文本。按 `i`, `a`, `o` 等键从正常模式进入。按 `Esc` 返回正常模式。
    3. **命令模式 (Command Mode)**: 在正常模式下按 `:` 进入，用于保存、退出、搜索等。
- **常用操作**
    - `dd`: 删除整行。
    - `yy`: 复制整行。
    - `p`: 粘贴。
    - `u`: 撤销。
    - `Ctrl + r`: 重做（反撤销）。
    - `:w`: 保存。
    - `:q`: 退出。
    - `:wq`: 保存并退出。
    - `:q!`: 强制退出（不保存）。

### 7. 环境配置与解压缩

- **配置文件**
    - `.bashrc` 或 `.profile`: 用户家目录下的隐藏文件，用于定义用户的环境变量和别名。
    - `export PATH=$PATH:/path/to/my/bin`: 临时将一个新路径添加到 `PATH` 环境变量中，使其下的可执行文件能被直接调用。将此行写入 `.bashrc` 可使其永久生效（需 `source ~/.bashrc` 或重开终端）。
- **别名 `alias`**
为长命令创建快捷方式，写入 `.bashrc` 中。
    
    ```bash
    alias ll='ls -alh'
    alias myip='curl ifconfig.me'
    ```
    
- **解压缩**
    - **tar** (常用于 `.tar.gz` 或 `.tgz` 文件)
        - 解压: `tar -xzvf archive.tar.gz`
        - 压缩: `tar -czvf archive.tar.gz directory_to_compress/`
    - **zip/unzip**
        - 解压: `unzip archive.zip`
        - 压缩: `zip -r archive.zip directory_to_compress/`

### 8. 让程序在后台运行

当需要运行耗时很长的任务，并且希望关闭终端后程序依然运行时，以下工具至关重要。

- **`nohup`**
"No Hang Up" 的缩写，让命令在退出终端后继续运行，默认输出会重定向到 `nohup.out` 文件。
    
    ```bash
    nohup python my_long_task.py &
    ```
    
    `&` 符号表示将命令放到后台执行。
    
- **`screen`**
一个更强大的工具，可以创建多个虚拟终端会话，并随时分离（detach）和重新连接（reattach）。
    1. **新建会话**: `screen -S my_session_name`
    2. **在会话中运行程序**: `python my_app.py`
    3. **分离会话**: 按 `Ctrl + a` 然后按 `d`。此时你可以安全地关闭终端。
    4. **列出所有会话**: `screen -ls`
    5. **重新连接会话**: `screen -r my_session_name`

## windows
### 查看当前在 cmd 中使用的 python 版本的路径
```shell
# 查看当前在 cmd 中使用的 python 版本的路径
python -c "import sys; print(sys.executable)"
  # 由于我用的是 python 3.10, 所以打印信息如下:
    # E:\programs\python\Python310\python.exe

# 此外, 直接去环境变量 PATH 中也可以查看默认使用的 python
  # 注意: 如果 PATH 中写入了多个 python 路径, 只有排在上面的会被用到.

```

### 查看所有已安装 python 版本的路径
```shell
# 查看所有已安装 python 版本的路径
# python 3.6 以上的版本均支持一个共同的语法, 以 "py" 开头, 后跟一些参数 (具体
# 可查看 `py --help`). 该命令无需添加环境变量均可使用.
py --list-paths
  # 例如我在电脑上自定义目录安装了 python 2.7, 3.8 ~ 3.10, 可以看到以下信息.
  # (注: 末尾有 * 号的表示当前默认使用的版本)
    # Installed Pythons found by py Launcher for Windows
    # -3.10-64    E:\programs\python\Python310\python.exe *
    # -3.9-64     E:\programs\python\Python39\python.exe
    # -3.8-64     E:\programs\python\Python38\python.exe
    # -2.7-64     E:\programs\python\Python27\python.exe

# 注意: "py" 命令仅在 windows 上可用.
# 相关阅读: https://docs.python.org/3/using/windows.html#launcher

```

## Linux
### 查看当前使用的 python 路径
```shell
# 查看当前使用的 python 路径
which python3
  # /usr/bin/python3
# 备注: `which python` (不是 `which python3`) 指向的是 python 2. 仅在
# 默认使用的是 python 2 时才有效. 比如, ubuntu 20 自带的是 python 3.8, 
# 使用该命令就无效.

# 此外也可以通过 pip 的版本信息来定位 (需要 apt 先安装 pip)
pip --version  # 或者 pip3 --version
  # pip 20.0.2 from /usr/lib/python3/dist-packages/pip (python 3.8)

```
### 列出所有 python 版本路径
```shell
# 列出所有 python 版本路径
whereis python
  # (注: 打印的结果是没有换行的. 为了便于展示, 我在这里把它们逐行列出来)
    # python: 
      # /usr/lib/python2.7
      #
      # /etc/python3.8
      # /usr/bin/python3.8
      # /usr/bin/python3.8-config
      # /usr/include/python3.8
      # /usr/lib/python3.8
      # /usr/local/lib/python3.8
      # 
      # /etc/python3.9
      # /usr/bin/python3.9
      # /usr/lib/python3.9
      # /usr/local/lib/python3.9
# 此外, 使用 `whereis python2`, `whereis python3` 可以过滤上述结果.

```

---
title: "Python 函数与 Lambda 表达式"
date: 2022-05-01
description: "拆解 Python 函数的参数、作用域、函数对象与闭包，并通过 Lambda 表达式掌握轻量函数的适用场景。"
categories: ["notes"]
topics: ["engineering"]
tags: ["python"]
series: ["python-base"]
series_order: 3
showAuthor: false
aliases: ["/blogs/python/base/python-function-lambda/"]
---


## 函数

### 函数简介

- 函数以`def`关键词开头，后接函数名和圆括号()。
- 函数执行的代码以冒号起始，并且缩进。
- return [表达式] 结束函数，选择性地返回一个值给调用方。不带表达式的return相当于返回`None`。
    
    ```python
    def functionname (parameters):
    		"函数_文档字符串"
        function_suite
        return expression
    
    ```
    
- python的函数具有非常灵活多样的参数，既可以实现简单的调用又可以传入复杂的参数。python允许函数调用时参数顺序与声明时不一致，解释器能够用参数名匹配参数值。
    - 位置参数 (positional argument)
    - 默认参数 (default argument)
    - 可变参数 (variable argument)：`args`，可以是零个或任意个，自动组装成元组，并且会存放所有未命名的变量参数。
    - 关键字参数 (keyword argument)：`**kwargs`，可以是零个或任意个，自动组装成字典。
        
        ```python
        def printinfo(arg1, *args, **kwargs):
            print(arg1)
            print(args)
            print(kwargs)
        
        printinfo(70, 60, 50)
        # 70
        # (60, 50)
        # {}
        printinfo(70, 60, 50, a=1, b=2)
        # 70
        # (60, 50)
        # {'a': 1, 'b': 2}
        
        ```
        
    - 命名关键字参数 (keyword-only argument)：`nkw`，只能通过参数名传入。
    - 参数组合：位置参数、`*args`、命名关键字参数和 `**kwargs` 可以一起使用，但是顺序不能改变：位置参数、`*args`、命名关键字参数、`**kwargs`。
        
        可变参数和命名关键字参数可以同时使用，命名关键字参数必须写在 `*args` 之后。
        
        ```python
        def printinfo(arg1, *args, nkw, nkw1, **kwargs):
            print(arg1)
            print(args)
            print(nkw)
            print(nkw1)
            print(kwargs)
        
        printinfo(70, nkw=10, nkw1=11, a=1, b=2)
        # 70
        # ()
        # 10
        # 11
        # {'a': 1, 'b': 2}
        
        printinfo(70, 10, 11, nkw=12, nkw1=13, a=1, b=2)
        # 70
        # (10, 11)
        # 12
        # 13
        # {'a': 1, 'b': 2}
        # 10 和 11 被 *args 收集，nkw 和 nkw1 通过参数名传入
        
        ```
        

### 变量作用域

- Python 中，程序的变量并不是在哪个位置都可以访问的，访问权限决定于这个变量是在哪里赋值的。
- 定义在函数内部的变量拥有局部作用域，该变量称为局部变量。
- 定义在函数外部的变量拥有全局作用域，该变量称为全局变量。
- 局部变量只能在其被声明的函数内部访问，而全局变量可以在整个程序范围内访问。
- **当内部作用域想修改外部作用域的变量时，就要用到`global`和`nonlocal`关键字。**
- 内嵌函数
    
    ```python
    def outer():
        print('outer函数在这被调用')
    
        def inner():
            print('inner函数在这被调用')
    
        inner()  # 该函数只能在outer函数内部被调用
    
    outer()
    # outer函数在这被调用
    # inner函数在这被调用
    
    ```
    

### 函数对象

函数对象是指函数可以被当作「数据」来处理

- 函数可以被引用
- 函数可以作为容器类型的元素
- 函数可以作为参数传入另外一个函数
- 函数的返回值可以是一个函数

参考文章：
[python API](https://docs.python.org/zh-cn/3.7/c-api/function.html)

### 闭包

- 是函数式编程的一个重要的语法结构，是一种特殊的内嵌函数。
- 如果在一个内部函数里对外层非全局作用域的变量进行引用，那么内部函数就被认为是闭包。
- 通过闭包可以访问外层非全局作用域的变量，这个作用域称为 **闭包作用域**。

```python
def make_counter(init):
	counter = [init]
	def inc():
		counter[0] += 1
	def dec():
		counter[0] -= 1
	def get():
		return counter[0]
	def reset():
		counter[0] = init
	def nonloc():
		nonlocal counter # 使用关键字nonlocal可以修改闭包作用域中的变量
		counter = [9, 1]
		print(counter)
	return inc, dec, get, reset, nonloc

inc, dec, get, reset, nonloc = make_counter(0)
inc()
inc()
inc() # 三次调用inc()函数， 不用重复赋值
print(get())  # 3
dec()
print(get())  # 2
reset()
print(get())  # 0

inc()
inc()
print(get()) # 2
dec()
print(get()) # 1
nonloc() # [9,1]
print(get()) # 9

```

参考文章：[函数对象与闭包](https://zhuanlan.zhihu.com/p/109056932)

## Lambda表达式

在 Python 里有两类函数：

- 第一类：用 `def` 关键词定义的正规函数
- 第二类：用 `lambda` 关键词定义的匿名函数

lambda 表达式（有时称为 lambda 构型）被用于创建匿名函数。 表达式 `lambda parameters: expression` 会产生一个函数对象 ，没有函数名。

1. `lambda` - 定义匿名函数的关键词。
2. `parameters` - 函数参数，它们可以是位置参数、默认参数、关键字参数，和正规函数里的参数类型一样。
3. `:`冒号，在函数参数和表达式中间要加个冒号。
4. `expression` - 只是一个表达式，输入函数参数，输出一些值。

注意：

1. `expression` 中没有 return 语句，因为 lambda 不需要它来返回，表达式本身结果就是返回值。
2. 匿名函数与正规函数一样，按照 LEGB 规则查找名称，可以访问全局命名空间中的名称。
- 匿名函数的应用
    
    匿名函数 常常应用于函数式编程的高阶函数 (high-order function)中，主要有两种形式：
    
    - 参数是函数 (filter, map)
    - 返回值是函数 (closure)
    
    ```python
    # 在 filter和map函数中的应用：
    #   filter(function, iterable) 过滤序列，过滤掉不符合条件的元素，返回一个迭代器对象，如果要转换为列表，可以使用 list() 来转换。
    
    odd = lambda x: x % 2 == 1
    templist = filter(odd, [1, 2, 3, 4, 5, 6, 7, 8, 9])
    print(list(templist))  # [1, 3, 5, 7, 9]
    
    #  map(function, *iterables) 根据提供的函数对指定序列做映射。
    
    m1 = map(lambda x: x ** 2, [1, 2, 3, 4, 5])
    print(list(m1))
    # [1, 4, 9, 16, 25]
    
    m2 = map(lambda x, y: x + y, [1, 3, 5, 7, 9], [2, 4, 6, 8, 10])
    print(list(m2))
    # [3, 7, 11, 15, 19]
    
    ```

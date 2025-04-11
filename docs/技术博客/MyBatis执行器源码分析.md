# MyBatis 执行器源码分析：深入理解批量操作性能瓶颈

## 1. 引言

在使用 MyBatis 进行批量数据操作时，我们经常会遇到性能瓶颈问题。为了解决这些问题，我们需要深入理解 MyBatis 的执行机制，特别是其核心组件 —— Executor（执行器）的工作原理。本文将通过源码分析，揭示 MyBatis 执行器的内部工作机制，并针对批量插入操作提供优化建议。

## 2. MyBatis 执行架构概述

在深入分析 Executor 之前，我们先了解 MyBatis 的整体执行架构：

![MyBatis执行架构](https://mybatis.org/images/mybatis-logo.png)

MyBatis 的执行流程主要包括以下几个核心组件：

1. **SqlSession**：提供给用户的 API 接口层
2. **Executor**：执行器，负责整体执行流程
3. **StatementHandler**：语句处理器，负责 SQL 语句的处理和执行
4. **ParameterHandler**：参数处理器，负责参数的设置
5. **ResultSetHandler**：结果集处理器，负责结果的处理

其中，Executor 是整个执行过程的核心，负责调度其他组件完成 SQL 的执行。

## 3. Executor 接口及其实现

### 3.1 Executor 接口定义

Executor 接口定义了 MyBatis 执行 SQL 的核心方法，位于 `org.apache.ibatis.executor` 包中：

```java
public interface Executor {
  // 执行更新操作（插入、更新、删除）
  int update(MappedStatement ms, Object parameter) throws SQLException;
  
  // 执行查询操作
  <E> List<E> query(MappedStatement ms, Object parameter, RowBounds rowBounds, 
                   ResultHandler resultHandler) throws SQLException;
  <E> List<E> query(MappedStatement ms, Object parameter, RowBounds rowBounds, 
                   ResultHandler resultHandler, CacheKey cacheKey, BoundSql boundSql) throws SQLException;
  
  // 执行游标查询
  <E> Cursor<E> queryCursor(MappedStatement ms, Object parameter, RowBounds rowBounds) throws SQLException;
  
  // 刷新批处理语句
  List<BatchResult> flushStatements() throws SQLException;
  
  // 提交事务
  void commit(boolean required) throws SQLException;
  
  // 回滚事务
  void rollback(boolean required) throws SQLException;
  
  // 其他方法...
}
```

### 3.2 Executor 的主要实现类

MyBatis 提供了几种不同的 Executor 实现，以满足不同的需求：

1. **BaseExecutor**：抽象基类，提供了通用功能
2. **SimpleExecutor**：最常用的实现，每次执行创建一个新的 Statement
3. **ReuseExecutor**：重用 Statement 的实现
4. **BatchExecutor**：批处理实现，用于批量操作
5. **CachingExecutor**：带缓存的实现，通常作为装饰器包装其他 Executor

## 4. 执行更新操作的源码分析

我们以 `update` 方法为例，分析 MyBatis 执行插入、更新和删除操作的过程。

### 4.1 BaseExecutor 中的 update 实现

```java
@Override
public int update(MappedStatement ms, Object parameter) throws SQLException {
  ErrorContext.instance().resource(ms.getResource()).activity("executing an update").object(ms.getId());
  if (closed) {
    throw new ExecutorException("Executor was closed.");
  }
  clearLocalCache();
  return doUpdate(ms, parameter);
}
```

BaseExecutor 的 update 方法主要做了三件事：
1. 设置错误上下文（用于异常信息）
2. 清除本地缓存
3. 调用抽象方法 doUpdate 执行实际的更新操作

### 4.2 SimpleExecutor 中的 doUpdate 实现

```java
@Override
public int doUpdate(MappedStatement ms, Object parameter) throws SQLException {
  Statement stmt = null;
  try {
    Configuration configuration = ms.getConfiguration();
    // 创建 StatementHandler
    StatementHandler handler = configuration.newStatementHandler(this, ms, parameter, RowBounds.DEFAULT, null, null);
    // 准备 Statement
    stmt = prepareStatement(handler, ms.getStatementLog());
    // 执行更新操作
    return handler.update(stmt);
  } finally {
    closeStatement(stmt);
  }
}
```

SimpleExecutor 的 doUpdate 方法主要做了三件事：
1. 创建 StatementHandler
2. 准备 Statement
3. 调用 StatementHandler.update 执行更新操作

### 4.3 prepareStatement 方法

```java
private Statement prepareStatement(StatementHandler handler, Log statementLog) throws SQLException {
  Statement stmt;
  Connection connection = getConnection(statementLog);
  stmt = handler.prepare(connection, transaction.getTimeout());
  handler.parameterize(stmt);
  return stmt;
}
```

prepareStatement 方法主要做了三件事：
1. 获取数据库连接
2. 调用 StatementHandler.prepare 准备 Statement
3. 调用 StatementHandler.parameterize 设置参数

### 4.4 StatementHandler.update 方法

PreparedStatementHandler 的 update 方法实现如下：

```java
@Override
public int update(Statement statement) throws SQLException {
  PreparedStatement ps = (PreparedStatement) statement;
  ps.execute();
  int rows = ps.getUpdateCount();
  Object parameterObject = boundSql.getParameterObject();
  KeyGenerator keyGenerator = mappedStatement.getKeyGenerator();
  keyGenerator.processAfter(executor, mappedStatement, ps, parameterObject);
  return rows;
}
```

## 5. BatchExecutor 的实现分析

对于批量操作，MyBatis 提供了专门的 BatchExecutor 实现：

```java
@Override
public int doUpdate(MappedStatement ms, Object parameterObject) throws SQLException {
  final Configuration configuration = ms.getConfiguration();
  final StatementHandler handler = configuration.newStatementHandler(this, ms, parameterObject, RowBounds.DEFAULT, null, null);
  final BoundSql boundSql = handler.getBoundSql();
  final String sql = boundSql.getSql();
  final Statement stmt;
  
  // 检查当前批处理是否可以合并
  if (sql.equals(currentSql) && ms.equals(currentStatement)) {
    // 可以合并，复用之前的 Statement
    int last = statementList.size() - 1;
    stmt = statementList.get(last);
    applyTransactionTimeout(stmt);
    handler.parameterize(stmt);
    BatchResult batchResult = batchResultList.get(last);
    batchResult.addParameterObject(parameterObject);
  } else {
    // 不能合并，创建新的 Statement
    Connection connection = getConnection(ms.getStatementLog());
    stmt = handler.prepare(connection, transaction.getTimeout());
    handler.parameterize(stmt);
    currentSql = sql;
    currentStatement = ms;
    statementList.add(stmt);
    batchResultList.add(new BatchResult(ms, sql, parameterObject));
  }
  
  // 添加到批处理
  handler.batch(stmt);
  return BATCH_UPDATE_RETURN_VALUE; // 返回一个特殊值，表示批处理模式
}
```

BatchExecutor 的特点是：
1. 尝试合并相同的 SQL 语句
2. 使用 JDBC 的批处理功能（addBatch）
3. 延迟执行，直到调用 flushStatements 或 commit


## 参考资料

1. MyBatis 官方文档：https://mybatis.org/mybatis-3/
2. MyBatis GitHub 仓库：https://github.com/mybatis/mybatis-3
3. MyBatis 源码（版本 3.5.6）

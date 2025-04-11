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

## 6. 批量插入操作的性能瓶颈分析

通过 TimeMonitorInterceptor 拦截器的日志分析，我们发现批量插入 57 条记录时的性能瓶颈主要在以下环节：

### 6.1 参数化处理耗时（550ms，占总时间的 18%）

这发生在 `StatementHandler.parameterize(stmt)` 方法中，主要工作是将 Java 对象转换为 SQL 参数。对于批量插入，需要处理大量参数（57条记录 × 15个字段 = 855个参数），涉及大量的反射操作和类型转换。

### 6.2 update 方法到实际 SQL 执行之间的"黑洞时间"（约2.3秒，占总时间的 77%）

从 `parameterize` 完成到实际 SQL 执行（p6spy 记录）有约2.3秒的间隔，这个间隔主要发生在以下几个环节：

#### 6.2.1 获取数据库连接

在 `getConnection(statementLog)` 方法中获取数据库连接。如果连接池资源紧张，可能需要等待。

#### 6.2.2 事务处理

事务的开启、提交或回滚可能引入延迟，特别是在分布式事务或主从切换的情况下。

#### 6.2.3 数据源切换

如果使用了 MasterSlaveAutoRoutingPluginTiering 等拦截器进行主从切换，数据源切换可能需要时间，特别是需要建立新连接时。

### 6.3 关键时间点

- 21:22:42.080 - prepare 阶段开始
- 21:22:42.654 - parameterize 阶段完成（耗时 550ms）
- 21:22:45.010 - 第一条 SQL 执行记录（p6spy）
- 21:22:45.013 - 第二条 SQL 执行记录（p6spy）
- 21:22:45.014 - update 方法完成（总耗时 2358ms）

## 7. 批量操作性能优化建议

基于源码分析，我们可以从以下几个方面优化批量操作性能：

### 7.1 优化连接池配置

```properties
# 增加最大连接数
spring.datasource.hikari.maximum-pool-size=20
# 增加最小空闲连接数，减少连接获取时间
spring.datasource.hikari.minimum-idle=10
# 减少连接超时时间
spring.datasource.hikari.connection-timeout=10000
```

### 7.2 使用 BatchExecutor 代替 SimpleExecutor

在 Spring 配置中设置默认的 ExecutorType 为 BATCH：

```java
@Bean
public SqlSessionFactory sqlSessionFactory(DataSource dataSource) throws Exception {
    SqlSessionFactoryBean factoryBean = new SqlSessionFactoryBean();
    factoryBean.setDataSource(dataSource);
    factoryBean.setDefaultExecutorType(ExecutorType.BATCH);
    return factoryBean.getObject();
}
```

或者在代码中显式使用 BatchExecutor：

```java
try (SqlSession sqlSession = sqlSessionFactory.openSession(ExecutorType.BATCH)) {
    Mapper mapper = sqlSession.getMapper(Mapper.class);
    // 执行批量操作
    sqlSession.flushStatements();
    sqlSession.commit();
}
```

### 7.3 优化批量大小

将大批量操作拆分为多个较小的批次（每批10-20条记录）：

```java
@Transactional
public void batchInsert(List<Record> records) {
    SqlSession sqlSession = sqlSessionFactory.openSession(ExecutorType.BATCH);
    try {
        RecordMapper mapper = sqlSession.getMapper(RecordMapper.class);
        for (int i = 0; i < records.size(); i++) {
            mapper.insert(records.get(i));
            if (i > 0 && i % 20 == 0) {
                sqlSession.flushStatements();
            }
        }
        sqlSession.flushStatements();
        sqlSession.commit();
    } finally {
        sqlSession.close();
    }
}
```

### 7.4 监控和优化拦截器

在拦截器中添加性能监控点，记录各个阶段的耗时：

```java
@Intercepts({
    @Signature(type = Executor.class, method = "update", args = {MappedStatement.class, Object.class})
})
public class PerformanceInterceptor implements Interceptor {
    @Override
    public Object intercept(Invocation invocation) throws Throwable {
        long start = System.currentTimeMillis();
        try {
            return invocation.proceed();
        } finally {
            long end = System.currentTimeMillis();
            log.info("Executor.update 耗时: {} ms", (end - start));
        }
    }
}
```

### 7.5 使用 JDBC 批处理

对于大批量操作，考虑直接使用 JDBC 批处理，绕过 MyBatis 的部分开销：

```java
@Autowired
private DataSource dataSource;

public void batchInsertWithJdbc(List<Record> records) throws SQLException {
    String sql = "INSERT INTO table (col1, col2) VALUES (?, ?)";
    try (Connection conn = dataSource.getConnection();
         PreparedStatement ps = conn.prepareStatement(sql)) {
        
        for (Record record : records) {
            ps.setString(1, record.getCol1());
            ps.setString(2, record.getCol2());
            ps.addBatch();
        }
        ps.executeBatch();
    }
}
```

## 8. 总结

通过对 MyBatis Executor 源码的分析，我们深入理解了 MyBatis 执行 SQL 的内部机制，特别是批量操作的执行流程。在实际应用中，批量操作的性能瓶颈主要来自参数处理、连接获取和事务处理等环节。

针对这些瓶颈，我们可以通过优化连接池配置、使用 BatchExecutor、调整批量大小、监控拦截器性能以及使用 JDBC 批处理等方式来提高批量操作的性能。

希望本文的分析能够帮助您更好地理解 MyBatis 的执行机制，并在实际开发中优化批量操作性能。

## 参考资料

1. MyBatis 官方文档：https://mybatis.org/mybatis-3/
2. MyBatis GitHub 仓库：https://github.com/mybatis/mybatis-3
3. MyBatis 源码（版本 3.5.6）

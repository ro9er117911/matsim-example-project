# PT转换流程 - 早停策略

## 概述

PT转换流程包含4个阶段，每个阶段都有独立的超时保护和早停机制。

## 流程阶段与超时时间

| 阶段 | 任务 | 超时时间 | 预期耗时 | 资源消耗 |
|------|------|----------|----------|----------|
| 1️⃣ | Maven打包 | 5分钟 | 1-2分钟 | 中等CPU，低内存 |
| 2️⃣ | GTFS转换 | 30分钟 | 5-15分钟 | 高内存(8G) |
| 3️⃣ | PT映射 | 2小时 | 30-90分钟 | 极高内存(12G)，高CPU |
| 4️⃣ | 验证 | 10分钟 | 2-5分钟 | 中等内存(4G) |

**总超时**: 4小时（用户命令中设定）

## 早停触发条件

### 自动停止

1. **超时停止** - `timeout` 命令到达时间限制
2. **内存不足** - JVM OutOfMemoryError
3. **致命错误** - Java异常或错误退出码
4. **磁盘空间不足** - 写入失败

### 手动停止

在任何阶段都可以：
- **Ctrl+C** - 发送SIGINT信号
- **kill -15 <pid>** - 优雅停止
- **kill -9 <pid>** - 强制停止（最后手段）

## 分阶段执行策略

### 推荐：逐阶段运行

不要一次运行所有阶段，而是**分开运行并验证**：

```bash
# 阶段1: 仅打包
./mvnw clean package

# 检查JAR
ls -lh target/*.jar

# 阶段2: 仅GTFS转换
timeout 30m java -Xmx8g -cp target/matsim-example-project-0.0.1-SNAPSHOT.jar:pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.project.tools.GtfsToMatsim \
  --gtfsZip pt2matsim/combine/output/merged_gtfs.zip \
  --network pt2matsim/output_v1/network-prepared.xml.gz \
  --outDir pt2matsim/output_v1 \
  --targetCRS EPSG:3826 | tee pt2matsim/output_v1/gtfs_to_matsim.log

# 验证输出
ls -lh pt2matsim/output_v1/transitSchedule*.xml*

# 阶段3: 仅PT映射
timeout 2h java -Xmx12g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.PublicTransitMapper \
  pt2matsim/work/ptmapper-config-merged.xml | tee pt2matsim/output_v1/ptmapper.log

# 验证映射
ls -lh pt2matsim/output_v1/*-mapped.xml*

# 阶段4: 验证
timeout 10m java -Xmx4g -cp pt2matsim/work/pt2matsim-25.8-shaded.jar \
  org.matsim.pt2matsim.run.CheckMappedSchedulePlausibility \
  pt2matsim/output_v1/network-with-pt.xml.gz \
  pt2matsim/output_v1/transitSchedule-mapped.xml.gz | tee pt2matsim/output_v1/check_plausibility.log
```

## 资源监控

### 在运行前检查资源

```bash
# 检查可用内存（需要至少12GB）
free -h

# 检查磁盘空间（需要至少10GB）
df -h .

# 检查CPU核心数
nproc
```

### 运行时监控

在**另一个终端**中：

```bash
# 监控内存使用
watch -n 5 'free -h'

# 监控Java进程
watch -n 5 'ps aux | grep java'

# 监控磁盘使用
watch -n 10 'df -h .'

# 查看实时日志
tail -f pt2matsim/output_v1/*.log
```

## 早停后的检查清单

### 如果阶段1（Maven打包）失败

- [ ] 检查网络连接（Maven需要下载依赖）
- [ ] 检查磁盘空间
- [ ] 查看日志: `cat pt2matsim/output_v1/maven_package.log`
- [ ] 尝试: `./mvnw clean` 后重新打包

### 如果阶段2（GTFS转换）超时

- [ ] 检查GTFS文件大小: `ls -lh pt2matsim/combine/output/merged_gtfs.zip`
- [ ] 增加超时: 从30分钟→60分钟
- [ ] 增加内存: `-Xmx8g` → `-Xmx12g`
- [ ] 检查日志中的警告: `grep WARN pt2matsim/output_v1/gtfs_to_matsim.log`

### 如果阶段3（PT映射）超时或失败

这是**最耗资源**的阶段，最可能超时：

- [ ] 检查网络大小
  ```bash
  gunzip -c pt2matsim/output_v1/network-prepared.xml.gz | wc -l
  ```
- [ ] 检查站点数量
  ```bash
  grep -o '<stopFacility' pt2matsim/output_v1/transitSchedule.xml | wc -l
  ```
- [ ] 调整mapper配置参数:
  ```xml
  <!-- 减少候选数量 -->
  <param name="nLinkThreshold" value="6"/>  <!-- 从12降到6 -->

  <!-- 减少搜索距离 -->
  <param name="maxLinkCandidateDistance" value="200.0"/>  <!-- 从500降到200 -->

  <!-- 增加线程数 -->
  <param name="numOfThreads" value="8"/>  <!-- 根据CPU核心数 -->
  ```
- [ ] 增加超时: 2小时 → 4小时
- [ ] 增加内存和CPU:
  ```bash
  java -Xmx16g -Djava.util.concurrent.ForkJoinPool.common.parallelism=8 ...
  ```

### 如果OutOfMemoryError

```
java.lang.OutOfMemoryError: Java heap space
```

解决方案：
1. 增加堆内存: `-Xmx12g` → `-Xmx16g` → `-Xmx24g`
2. 减少工作负载（减少GTFS线路，减小网络范围）
3. 使用更强大的机器

## 性能优化建议

### CPU优化

```bash
# 设置JVM并行度（根据CPU核心数）
export JAVA_OPTS="-Djava.util.concurrent.ForkJoinPool.common.parallelism=8"

# 或在命令中直接指定
java -Xmx12g -Djava.util.concurrent.ForkJoinPool.common.parallelism=8 ...
```

### 内存优化

```bash
# 设置初始堆大小等于最大堆大小（减少GC）
java -Xms12g -Xmx12g ...

# 使用G1 GC（适合大堆）
java -Xmx12g -XX:+UseG1GC ...
```

### 磁盘I/O优化

```bash
# 使用tmpfs（如果内存充足）
mkdir -p /tmp/matsim_temp
export JAVA_OPTS="-Djava.io.tmpdir=/tmp/matsim_temp"
```

## 紧急停止程序

### 优雅停止

```bash
# 1. 找到Java进程ID
ps aux | grep "java.*pt2matsim"

# 2. 发送SIGTERM（给进程时间清理）
kill -15 <PID>

# 3. 等待10秒

# 4. 检查是否还在运行
ps -p <PID>
```

### 强制停止

```bash
# 如果优雅停止无效，使用SIGKILL
kill -9 <PID>

# 清理孤儿进程
pkill -9 -f "java.*pt2matsim"
```

## 检查点与恢复

PT映射器不支持检查点，如果中断需要**完全重新运行**。

但可以保存中间结果：

```bash
# 阶段2完成后，立即备份
cp pt2matsim/output_v1/transitSchedule.xml \
   pt2matsim/output_v1/transitSchedule.xml.backup

# 如果阶段3失败，不需要重新运行阶段2
```

## 预期输出大小

正常完成后的文件大小参考：

| 文件 | 预期大小 | 说明 |
|------|----------|------|
| `transitSchedule.xml` | 1-10MB | GTFS转换结果 |
| `transitVehicles.xml` | 100KB-1MB | 车辆定义 |
| `transitSchedule-mapped.xml.gz` | 1-20MB | 映射后的schedule |
| `network-with-pt.xml.gz` | 5-50MB | 包含PT的网络 |
| `*.log` | 100KB-10MB | 日志文件 |

## 故障排除快速参考

| 问题 | 快速检查 | 解决方案 |
|------|----------|----------|
| 超时 | `ps aux \| grep java` | 增加超时时间 |
| 内存不足 | `free -h` | 增加-Xmx |
| 磁盘满 | `df -h` | 清理空间 |
| CPU 100% | `top` | 这是正常的（计算密集） |
| 无进度 | 查看日志 | 检查是否卡住 |

## 最佳实践

✅ **DO**:
- 分阶段运行，每阶段验证
- 监控资源使用
- 保存中间结果
- 使用充足的超时时间
- 从小数据集开始测试

❌ **DON'T**:
- 一次运行所有阶段
- 在资源不足的机器上运行
- 忽略警告日志
- 使用过短的超时
- 直接处理完整生产数据

## 云环境建议

如果本地资源不足，考虑使用云VM：

- **最小配置**: 4核CPU, 16GB RAM, 50GB磁盘
- **推荐配置**: 8核CPU, 32GB RAM, 100GB磁盘
- **大型场景**: 16核CPU, 64GB RAM, 200GB磁盘

推荐服务：
- AWS: c6i.2xlarge (8核, 16GB)
- GCP: n2-standard-8 (8核, 32GB)
- Azure: Standard_D8s_v3 (8核, 32GB)

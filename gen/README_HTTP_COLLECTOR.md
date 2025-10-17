HTTP Collector 简明说明

目标
- 在分布式 Scrapy 实例间汇聚 item 到单一文件（gen/collected_items.jsonl）。

组件
1. collector.py (FastAPI)
   - POST /items 接受单个 JSON item 并追加到 `gen/collected_items.jsonl`（JSON Lines）。
   - GET /health 返回服务状态。

2. http_pipeline.py (Scrapy pipeline 示例)
   - 在 Scrapy 项目中将 item POST 到 collector。

快速开始
1. 在虚拟环境中安装依赖：

```bash
python -m pip install -r gen/requirements.txt
```

2. 启动 collector（在项目根目录）：

```bash
uvicorn gen.collector:app --host 0.0.0.0 --port 8000
```

3. 在 Scrapy 项目的 `settings.py` 中启用 pipeline：

```python
ITEM_PIPELINES = {
    'yourproject.pipelines.HttpPostPipeline': 300,
}
HTTP_COLLECTOR_URL = 'http://localhost:8000/items'
```

4. 运行 spider（多实例同时运行），collector 会把 item 追加到 `gen/collected_items.jsonl`。

注意事项
- pipeline 使用同步 requests；若需要高吞吐可改为 aiohttp。
- collector 使用文件锁保护写入并发，适合中小规模测试。生产可使用 Redis/数据库或更健壮的存储。

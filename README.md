# 🔬 数字分析科学家

一个能够自动从原始行为数据中嗅探异常、发现机会并提供增长建议的智能数据分析平台。

## ✨ 功能特性

### 📊 智能洞察生成
- **异常检测**: 自动识别数据中的异常值和离群点
- **趋势分析**: 发现时间序列数据中的趋势变化
- **相关性分析**: 识别字段间的强相关关系
- **机会发现**: 挖掘潜在的业务增长机会
- **自动生成3-5个核心业务洞察卡片**

### 💬 自然语言查询
- 支持中文自然语言提问
- 自动转换为SQL查询
- 智能推荐最合适的图表类型
- 无需手动埋点配置或看板搭建

### 🗄️ 多数据源支持
- **CSV文件上传**: 支持拖拽上传，自动解析
- **数据库连接**: 支持 SQLite、MySQL、PostgreSQL
- 统一的数据访问接口

### 📈 可视化渲染
- 柱状图、折线图、饼图、散点图、直方图
- 智能图表类型推荐
- 交互式数据展示

## 🚀 快速开始

### 环境要求
- Python 3.8+
- pip 包管理器

### 安装步骤

1. **克隆项目**
```bash
cd Sentic
```

2. **创建虚拟环境（推荐）**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置你的 API Key 等信息
```

5. **启动应用**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

6. **访问应用**
- 前端界面: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 📖 使用指南

### 1. 接入数据源

#### 方式一：上传CSV文件
1. 点击"上传CSV"标签页
2. 拖拽CSV文件到上传区域，或点击选择文件
3. 系统自动解析数据并创建数据源

#### 方式二：连接数据库
1. 点击"连接数据库"标签页
2. 选择数据库类型（SQLite/MySQL/PostgreSQL）
3. 填写连接信息
4. 点击"连接数据库"按钮

### 2. 生成业务洞察
1. 在"已连接"标签页选择一个数据源
2. 点击"生成洞察"按钮
3. 系统将自动分析数据，生成3-5个核心业务洞察卡片

### 3. 自然语言查询
1. 确保已选择数据源
2. 在对话框中输入问题，例如：
   - "显示DAU趋势"
   - "各渠道用户数量对比"
   - "转化率是多少"
   - "按日期统计订单数量"
3. 点击"发送"或按回车键
4. 系统将自动：
   - 理解自然语言问题
   - 生成对应的SQL查询
   - 执行查询并返回结果
   - 推荐并渲染最合适的图表

## 🔧 API 接口

### 数据源管理
- `POST /api/data-source/upload-csv` - 上传CSV文件
- `POST /api/data-source/connect` - 连接数据库
- `GET /api/data-source/list` - 获取数据源列表
- `GET /api/data-source/{id}` - 获取数据源详情
- `GET /api/data-source/{id}/preview` - 预览数据
- `DELETE /api/data-source/{id}` - 删除数据源
- `POST /api/data-source/{id}/query` - 执行SQL查询

### 业务洞察
- `POST /api/insights/generate/{data_source_id}` - 生成洞察
- `GET /api/insights/{data_source_id}` - 获取缓存的洞察
- `POST /api/insights/refresh/{data_source_id}` - 刷新洞察

### 对话查询
- `POST /api/chat/query` - 发送查询
- `GET /api/chat/conversation/{id}` - 获取会话历史
- `POST /api/chat/clear-conversation/{id}` - 清空会话

### 可视化
- `POST /api/visualization/generate` - 生成图表
- `GET /api/visualization/chart-types` - 获取支持的图表类型

## 🧪 运行测试

### 运行所有测试
```bash
pytest tests/ -v
```

### 运行特定测试
```bash
pytest tests/test_data_source_service.py -v
pytest tests/test_insight_service.py -v
pytest tests/test_chat_service.py -v
```

### 生成覆盖率报告
```bash
pytest tests/ --cov=app --cov-report=html
```

## 📁 项目结构

```
Sentic/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic 数据模型
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── data_source.py      # 数据源路由
│   │   ├── insights.py         # 洞察路由
│   │   ├── chat.py             # 对话路由
│   │   └── visualization.py    # 可视化路由
│   ├── services/
│   │   ├── __init__.py
│   │   ├── data_source_service.py   # 数据源服务
│   │   ├── insight_service.py       # 洞察服务
│   │   └── chat_service.py          # 对话服务
│   └── utils/
├── data/
│   ├── sample_user_data.csv    # 示例数据
│   └── uploads/                # 上传文件目录
├── static/                     # 静态文件
├── templates/
│   └── index.html              # 前端界面
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # pytest 配置
│   ├── test_data_source_service.py
│   ├── test_insight_service.py
│   └── test_chat_service.py
├── .env.example                # 环境变量示例
├── config.py                   # 配置管理
├── requirements.txt            # 依赖列表
└── README.md                   # 本文档
```

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API Key | 可选 |
| `OPENAI_MODEL` | 使用的模型 | gpt-4-turbo-preview |
| `DATABASE_URL` | 数据库连接URL | sqlite:///./test.db |
| `APP_NAME` | 应用名称 | 数字分析科学家 |
| `APP_VERSION` | 应用版本 | 1.0.0 |
| `DEBUG` | 调试模式 | True |
| `HOST` | 服务器主机 | 0.0.0.0 |
| `PORT` | 服务器端口 | 8000 |

### 数据源类型支持

| 类型 | 支持状态 | 说明 |
|------|----------|------|
| CSV文件 | ✅ 完全支持 | 拖拽上传，自动解析 |
| SQLite | ✅ 完全支持 | 轻量级文件数据库 |
| MySQL | ✅ 完全支持 | 需要安装 pymysql |
| PostgreSQL | ✅ 完全支持 | 需要安装 psycopg2-binary |

## 🎯 洞察类型说明

### 🔴 异常检测 (Anomaly)
- 识别离群值和异常数据点
- 使用 Z-score 和孤立森林算法
- 检测数据录入错误或特殊业务事件

### 🟢 增长机会 (Opportunity)
- 发现小众但有潜力的用户群体
- 识别高表现和低表现类别差异
- 挖掘未被充分利用的市场机会

### 🔵 趋势分析 (Trend)
- 识别时间序列数据中的模式
- 检测日活跃度波动
- 发现周期性变化规律

### 🟣 相关性 (Correlation)
- 发现字段间的强相关关系
- 识别正相关和负相关
- 揭示潜在的业务因果关系

## 📊 示例数据

项目包含示例数据文件 `data/sample_user_data.csv`，包含以下字段：

| 字段 | 说明 |
|------|------|
| user_id | 用户ID |
| channel | 获客渠道 |
| signup_date | 注册日期 |
| last_active_date | 最后活跃日期 |
| purchase_amount | 购买金额 |
| purchase_count | 购买次数 |
| is_active | 是否活跃 |
| age_group | 年龄段 |
| region | 地区 |

可以使用此示例数据快速测试应用功能。

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📝 许可证

本项目采用 MIT 许可证。

## 🆘 常见问题

**Q: 支持哪些数据库？**
A: 目前支持 SQLite、MySQL 和 PostgreSQL。

**Q: 如何处理大文件？**
A: 系统使用流式处理，支持较大的 CSV 文件上传。

**Q: 是否需要 OpenAI API Key？**
A: 基础功能（异常检测、相关性分析等）不需要。高级自然语言理解功能（完整LLM集成）需要配置。

**Q: 数据是否安全？**
A: 所有数据处理都在本地进行，不会上传到第三方服务器（除非配置了LLM API）。

## 📞 支持

如有问题或建议，请：
1. 查看现有 Issues
2. 创建新 Issue 描述问题
3. 提交 Pull Request 贡献代码

---

**数字分析科学家** - 让数据说话，让决策更智能。

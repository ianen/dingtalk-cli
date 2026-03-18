# 钉钉文档 API 参考

本文件整理自原始 `dingtalk-document` skill 文档，供 `dingtalk-cli` 项目内独立维护。

## 认证

### 新版 accessToken

```http
POST https://api.dingtalk.com/v1.0/oauth2/accessToken
Content-Type: application/json

{
  "appKey": "<APP_KEY>",
  "appSecret": "<APP_SECRET>"
}
```

返回：

```json
{
  "accessToken": "xxx",
  "expireIn": 7200
}
```

后续请求头：

```http
x-acs-dingtalk-access-token: <accessToken>
```

### userId 换 unionId

```http
GET https://oapi.dingtalk.com/gettoken?appkey=<APP_KEY>&appsecret=<APP_SECRET>
```

```http
POST https://oapi.dingtalk.com/topapi/v2/user/get?access_token=<legacy_token>
Content-Type: application/json

{
  "userid": "<USER_ID>"
}
```

取返回中的 `result.unionid`。

## 知识库

### 查询知识库列表

```http
GET /v2.0/wiki/workspaces?operatorId=<UNION_ID>&maxResults=20&nextToken=<TOKEN>
```

### 查询知识库详情

```http
GET /v2.0/wiki/workspaces/{workspaceId}?operatorId=<UNION_ID>
```

## 节点

### 查询节点列表

```http
GET /v2.0/wiki/nodes?parentNodeId=<NODE_ID>&operatorId=<UNION_ID>&maxResults=50
```

### 查询单个节点

```http
GET /v2.0/wiki/nodes/{nodeId}?operatorId=<UNION_ID>
```

### 通过 URL 查询节点

```http
POST /v2.0/wiki/nodes/queryByUrl?operatorId=<UNION_ID>
Content-Type: application/json

{
  "url": "https://alidocs.dingtalk.com/i/nodes/<NODE_ID>",
  "operatorId": "<UNION_ID>"
}
```

## 普通文档

### 创建文档

```http
POST /v1.0/doc/workspaces/{workspaceId}/docs
Content-Type: application/json

{
  "operatorId": "<UNION_ID>",
  "docType": "DOC",
  "name": "<TITLE>"
}
```

返回中重点字段：

- `nodeId`
- `docKey`
- `workspaceId`
- `url`

### 读取文档 blocks

```http
GET /v1.0/doc/suites/documents/{docKey}/blocks?operatorId=<UNION_ID>
```

### 覆盖写入正文

```http
POST /v1.0/doc/suites/documents/{docKey}/overwriteContent
Content-Type: application/json

{
  "operatorId": "<UNION_ID>",
  "docContent": "# 标题\n\n正文",
  "contentType": "markdown"
}
```

### 删除文档

```http
DELETE /v1.0/doc/workspaces/{workspaceId}/docs/{nodeId}?operatorId=<UNION_ID>
```

## `.axls` 钉钉表格

识别条件：

- `type = FILE`
- `extension = axls`

### 列出工作表

```http
GET /v1.0/doc/workbooks/{workbookId}/sheets?operatorId=<UNION_ID>
```

### 读取工作表详情

```http
GET /v1.0/doc/workbooks/{workbookId}/sheets/{sheetId}?operatorId=<UNION_ID>
```

### 读取单元格区域

```http
GET /v1.0/doc/workbooks/{workbookId}/sheets/{sheetId}/ranges/{rangeAddress}?select=displayValues&operatorId=<UNION_ID>
```

## 成员管理

### 添加成员

```http
POST /v1.0/doc/workspaces/{workspaceId}/docs/{nodeId}/members
Content-Type: application/json

{
  "operatorId": "<UNION_ID>",
  "members": [
    {"id": "<USER_ID>", "roleType": "viewer|editor"}
  ]
}
```

### 更新成员权限

```http
PUT /v1.0/doc/workspaces/{workspaceId}/docs/{nodeId}/members/{memberId}
Content-Type: application/json

{
  "operatorId": "<UNION_ID>",
  "roleType": "viewer|editor"
}
```

### 移除成员

```http
DELETE /v1.0/doc/workspaces/{workspaceId}/docs/{nodeId}/members/{memberId}?operatorId=<UNION_ID>
```

## 常见错误

- `MissingoperatorId`：缺少 operatorId
- `paramError`：operatorId 类型错误
- `Forbidden.AccessDenied.AccessTokenPermissionDenied`：scope 不足
- `InvalidAction.NotFound`：接口路径或资源错误
- `Target document should be doc.`：把 `.axls` 当普通文档读取

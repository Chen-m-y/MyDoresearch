# 用户资料管理API接口文档

## 1. 获取用户资料

### 接口信息
- **接口路径**: `GET /api/auth/profile`
- **接口描述**: 获取当前登录用户的详细资料信息
- **认证要求**: 需要登录（Bearer Token 或 Cookie）

### 请求参数
无需请求参数

### 请求头
```
Authorization: Bearer <session_token>
Content-Type: application/json
```

### 请求示例
```bash
curl -X GET "http://127.0.0.1:5000/api/auth/profile" \
  -H "Authorization: Bearer iQRyIpSd9-kfhOCja9qlq9eaT6xBcIyIBlxGFAHp-vk" \
  -H "Content-Type: application/json"
```

### 响应格式

#### 成功响应 (200)
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@doresearch.com", 
    "created_at": "2025-08-08 16:27:23.508008",
    "last_login": "2025-08-08 17:30:15.123456",
    "active": true
  }
}
```

#### 失败响应 (401) - 未授权
```json
{
  "success": false,
  "error": "未授权访问，请先登录",
  "code": "UNAUTHORIZED"
}
```

#### 失败响应 (404) - 用户不存在
```json
{
  "success": false,
  "error": "用户不存在"
}
```

#### 失败响应 (500) - 服务器错误
```json
{
  "success": false,
  "error": "获取用户资料失败: 具体错误信息"
}
```

### 响应字段说明
| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 请求是否成功 |
| user.id | integer | 用户唯一标识ID |
| user.username | string | 用户名 |
| user.email | string | 用户邮箱 |
| user.created_at | string | 用户注册时间 (ISO格式) |
| user.last_login | string | 最后登录时间 (ISO格式) |
| user.active | boolean | 用户账户是否激活 |

---

## 2. 修改用户名

### 接口信息
- **接口路径**: `POST /api/auth/change-username`
- **接口描述**: 修改当前登录用户的用户名
- **认证要求**: 需要登录（Bearer Token 或 Cookie）

### 请求参数
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| new_username | string | 是 | 新用户名（3-20位字母、数字、下划线） |
| password | string | 是 | 当前密码（用于身份验证） |

### 请求头
```
Authorization: Bearer <session_token>
Content-Type: application/json
```

### 请求体
```json
{
  "new_username": "new_admin",
  "password": "admin123"
}
```

### 请求示例
```bash
curl -X POST "http://127.0.0.1:5000/api/auth/change-username" \
  -H "Authorization: Bearer iQRyIpSd9-kfhOCja9qlq9eaT6xBcIyIBlxGFAHp-vk" \
  -H "Content-Type: application/json" \
  -d '{
    "new_username": "new_admin",
    "password": "admin123"
  }'
```

### 响应格式

#### 成功响应 (200)
```json
{
  "success": true,
  "message": "用户名修改成功",
  "new_username": "new_admin"
}
```

#### 失败响应 (400) - 用户名格式错误
```json
{
  "success": false,
  "error": "用户名只能包含字母、数字和下划线，长度3-20位"
}
```

#### 失败响应 (400) - 用户名已被使用
```json
{
  "success": false,
  "error": "该用户名已被其他用户使用"
}
```

#### 失败响应 (400) - 密码错误
```json
{
  "success": false,
  "error": "当前密码错误"
}
```

#### 失败响应 (401) - 未授权
```json
{
  "success": false,
  "error": "未授权访问，请先登录",
  "code": "UNAUTHORIZED"
}
```

#### 失败响应 (500) - 服务器错误
```json
{
  "success": false,
  "error": "修改用户名失败: 具体错误信息"
}
```

---

## 3. 修改邮箱

### 接口信息
- **接口路径**: `POST /api/auth/change-email`
- **接口描述**: 修改当前登录用户的邮箱地址
- **认证要求**: 需要登录（Bearer Token 或 Cookie）

### 请求参数
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| new_email | string | 是 | 新邮箱地址（需要是有效邮箱格式） |
| password | string | 是 | 当前密码（用于身份验证） |

### 请求头
```
Authorization: Bearer <session_token>
Content-Type: application/json
```

### 请求体
```json
{
  "new_email": "newemail@example.com",
  "password": "admin123"
}
```

### 请求示例
```bash
curl -X POST "http://127.0.0.1:5000/api/auth/change-email" \
  -H "Authorization: Bearer iQRyIpSd9-kfhOCja9qlq9eaT6xBcIyIBlxGFAHp-vk" \
  -H "Content-Type: application/json" \
  -d '{
    "new_email": "newemail@example.com",
    "password": "admin123"
  }'
```

### 响应格式

#### 成功响应 (200)
```json
{
  "success": true,
  "message": "邮箱修改成功",
  "new_email": "newemail@example.com"
}
```

#### 失败响应 (400) - 邮箱格式错误
```json
{
  "success": false,
  "error": "邮箱格式不正确"
}
```

#### 失败响应 (400) - 邮箱已被使用
```json
{
  "success": false,
  "error": "该邮箱已被其他用户使用"
}
```

#### 失败响应 (400) - 密码错误
```json
{
  "success": false,
  "error": "当前密码错误"
}
```

#### 失败响应 (401) - 未授权
```json
{
  "success": false,
  "error": "未授权访问，请先登录",
  "code": "UNAUTHORIZED"
}
```

#### 失败响应 (500) - 服务器错误
```json
{
  "success": false,
  "error": "修改邮箱失败: 具体错误信息"
}
```

---

## 4. 修改密码

### 接口信息
- **接口路径**: `POST /api/auth/change-password`
- **接口描述**: 修改当前登录用户的密码
- **认证要求**: 需要登录（Bearer Token 或 Cookie）

### 请求参数
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| old_password | string | 是 | 当前密码 |
| new_password | string | 是 | 新密码（最少6位） |

### 请求头
```
Authorization: Bearer <session_token>
Content-Type: application/json
```

### 请求体
```json
{
  "old_password": "admin123",
  "new_password": "newpassword123"
}
```

### 请求示例
```bash
curl -X POST "http://127.0.0.1:5000/api/auth/change-password" \
  -H "Authorization: Bearer iQRyIpSd9-kfhOCja9qlq9eaT6xBcIyIBlxGFAHp-vk" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "admin123",
    "new_password": "newpassword123"
  }'
```

### 响应格式

#### 成功响应 (200)
```json
{
  "success": true,
  "message": "密码修改成功"
}
```

#### 失败响应 (400) - 请求数据为空
```json
{
  "success": false,
  "error": "请求数据为空"
}
```

#### 失败响应 (400) - 旧密码错误
```json
{
  "success": false,
  "error": "旧密码错误"
}
```

#### 失败响应 (400) - 新密码长度不足
```json
{
  "success": false,
  "error": "新密码长度至少6位"
}
```

#### 失败响应 (401) - 未授权
```json
{
  "success": false,
  "error": "未授权访问，请先登录",
  "code": "UNAUTHORIZED"
}
```

#### 失败响应 (500) - 服务器错误
```json
{
  "success": false,
  "error": "修改密码失败: 具体错误信息"
}
```

---

## 业务规则

### 用户名修改规则
1. **用户名格式要求**:
   - 长度为3-20个字符
   - 只能包含字母（a-z, A-Z）、数字（0-9）和下划线（_）
   - 不能包含空格或特殊字符

2. **唯一性检查**:
   - 新用户名不能与系统中其他用户的用户名重复
   - 可以修改为与当前用户名相同（无实际变化）

3. **安全验证**:
   - 必须提供当前密码进行身份验证
   - 密码验证失败则拒绝修改

### 邮箱修改规则
1. **邮箱格式验证**:
   - 必须符合标准邮箱格式 (如: user@example.com)
   - 支持国际域名和特殊字符

2. **唯一性检查**:
   - 新邮箱不能与系统中其他用户的邮箱重复
   - 可以修改为与当前邮箱相同（无实际变化）

3. **安全验证**:
   - 必须提供当前密码进行身份验证
   - 密码验证失败则拒绝修改

### 密码修改规则
1. **密码要求**:
   - 新密码最少6位字符
   - 支持字母、数字、特殊字符
   - 区分大小写

2. **安全机制**:
   - 必须提供正确的旧密码
   - 密码使用PBKDF2+SHA256+Salt加密存储
   - 修改成功后建议重新登录

## 使用场景
1. **用户资料维护** - 更新个人信息
2. **邮箱变更** - 更换联系邮箱
3. **安全管理** - 定期修改密码
4. **账户迁移** - 邮箱或密码迁移

## 注意事项
- 修改邮箱或密码后，当前会话仍然有效
- 邮箱修改会影响后续的登录（如果支持邮箱登录）
- 建议修改敏感信息后提示用户重新登录
- 所有修改操作都会记录到系统日志中

## JavaScript示例

```javascript
// 修改用户名
const changeUsername = async (newUsername, password) => {
  try {
    const response = await fetch('/api/auth/change-username', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        new_username: newUsername,
        password: password
      })
    });

    const result = await response.json();
    
    if (result.success) {
      alert(`用户名已修改为: ${result.new_username}`);
      // 可选：刷新用户资料显示
      await getUserProfile();
    } else {
      alert(`用户名修改失败: ${result.error}`);
    }
  } catch (error) {
    alert('网络错误，请稍后重试');
  }
};

// 修改邮箱
const changeEmail = async (newEmail, password) => {
  try {
    const response = await fetch('/api/auth/change-email', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        new_email: newEmail,
        password: password
      })
    });

    const result = await response.json();
    
    if (result.success) {
      alert(`邮箱已修改为: ${result.new_email}`);
      // 可选：刷新用户资料显示
      await getUserProfile();
    } else {
      alert(`邮箱修改失败: ${result.error}`);
    }
  } catch (error) {
    alert('网络错误，请稍后重试');
  }
};

// 修改密码
const changePassword = async (oldPassword, newPassword) => {
  try {
    const response = await fetch('/api/auth/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      },
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword
      })
    });

    const result = await response.json();
    
    if (result.success) {
      alert('密码修改成功！');
      // 可选：提示用户重新登录
    } else {
      alert(`密码修改失败: ${result.error}`);
    }
  } catch (error) {
    alert('网络错误，请稍后重试');
  }
};

// 获取用户资料
const getUserProfile = async () => {
  try {
    const response = await fetch('/api/auth/profile', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    });

    const result = await response.json();
    
    if (result.success) {
      console.log('用户资料:', result.user);
      return result.user;
    } else {
      console.error('获取用户资料失败:', result.error);
    }
  } catch (error) {
    console.error('网络错误:', error);
  }
};
```
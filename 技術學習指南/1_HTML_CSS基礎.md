# HTML/CSS 基礎指南

## 目錄
1. [HTML 基礎](#html-基礎)
2. [CSS 基礎](#css-基礎)
3. [Flexbox 布局](#flexbox-布局)
4. [Grid 布局](#grid-布局)
5. [實際應用案例](#實際應用案例)

## HTML 基礎

### HTML 文檔結構
基本的 HTML 文檔結構如下：
```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>網頁標題</title>
</head>
<body>
    <!-- 網頁內容 -->
</body>
</html>
```

### 常用 HTML 標籤
| 標籤 | 說明 | 範例 |
|------|------|------|
| `<h1>` - `<h6>` | 標題標籤 | `<h1>大標題</h1>` |
| `<p>` | 段落標籤 | `<p>這是一個段落</p>` |
| `<div>` | 區塊容器 | `<div>區塊內容</div>` |
| `<span>` | 行內容器 | `<span>行內內容</span>` |
| `<a>` | 超連結 | `<a href="URL">連結文字</a>` |
| `<img>` | 圖片 | `<img src="圖片.jpg" alt="描述">` |
| `<table>` | 表格 | `<table><tr><td>儲存格</td></tr></table>` |
| `<form>` | 表單 | `<form><input type="text"></form>` |

### 語意化標籤
```html
<header>網頁頭部</header>
<nav>導航欄</nav>
<main>
    <article>文章內容</article>
    <aside>側邊欄</aside>
</main>
<footer>頁尾</footer>
```

## CSS 基礎

### CSS 選擇器
| 選擇器 | 說明 | 範例 |
|--------|------|------|
| 元素選擇器 | 直接選擇 HTML 標籤 | `p { color: blue; }` |
| 類別選擇器 | 選擇特定 class | `.highlight { background: yellow; }` |
| ID 選擇器 | 選擇特定 ID | `#header { height: 80px; }` |
| 子元素選擇器 | 選擇直接子元素 | `div > p { margin: 10px; }` |
| 後代選擇器 | 選擇所有後代元素 | `div p { line-height: 1.6; }` |

### 常用 CSS 屬性
```css
.element {
    /* 尺寸 */
    width: 100px;
    height: 100px;
    
    /* 邊距 */
    margin: 10px;     /* 外邊距 */
    padding: 15px;    /* 內邊距 */
    
    /* 邊框 */
    border: 1px solid #000;
    border-radius: 5px;
    
    /* 文字樣式 */
    font-family: Arial, sans-serif;
    font-size: 16px;
    font-weight: bold;
    color: #333;
    
    /* 背景 */
    background-color: #fff;
    background-image: url('圖片.jpg');
    
    /* 定位 */
    position: relative;
    top: 0;
    left: 0;
}
```

### CSS 盒模型
![CSS Box Model](https://i.imgur.com/gKrVMeY.png)
```css
.box {
    box-sizing: border-box; /* 包含 padding 和 border */
    width: 200px;
    padding: 20px;
    border: 2px solid black;
    margin: 10px;
}
```

## Flexbox 布局

### Flexbox 基本概念
- 容器（Container）：設置 `display: flex`
- 項目（Items）：容器內的直接子元素

### 常用 Flexbox 屬性
| 屬性 | 值 | 說明 |
|------|-----|------|
| `flex-direction` | `row`, `column` | 主軸方向 |
| `justify-content` | `center`, `space-between` | 主軸對齊 |
| `align-items` | `center`, `stretch` | 交叉軸對齊 |
| `flex-wrap` | `wrap`, `nowrap` | 換行設置 |

### Flexbox 範例
```css
.container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
}

.item {
    flex: 1;
    margin: 10px;
}
```

## Grid 布局

### Grid 基本概念
- 容器：設置 `display: grid`
- 網格線：定義網格結構
- 網格區域：由網格線圍成的區域

### 常用 Grid 屬性
```css
.grid-container {
    display: grid;
    grid-template-columns: 1fr 2fr 1fr;
    grid-template-rows: auto;
    gap: 20px;
}

.grid-item {
    grid-column: 1 / 3;
    grid-row: 1 / 2;
}
```

### Grid 範例
建立一個響應式網格布局：
```css
.gallery {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    padding: 1rem;
}
```

## 實際應用案例

### 響應式導航欄
```html
<nav class="navbar">
    <div class="logo">Logo</div>
    <ul class="nav-links">
        <li><a href="#">首頁</a></li>
        <li><a href="#">關於</a></li>
        <li><a href="#">服務</a></li>
        <li><a href="#">聯絡我們</a></li>
    </ul>
</nav>
```

```css
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background-color: #f8f9fa;
}

.nav-links {
    display: flex;
    gap: 1rem;
    list-style: none;
}

@media (max-width: 768px) {
    .nav-links {
        display: none; /* 在移動設備上隱藏 */
    }
}
```

### 卡片網格布局
```html
<div class="card-grid">
    <div class="card">
        <img src="image1.jpg" alt="圖片1">
        <h3>標題1</h3>
        <p>描述文字...</p>
    </div>
    <!-- 更多卡片 -->
</div>
```

```css
.card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 2rem;
    padding: 2rem;
}

.card {
    border: 1px solid #ddd;
    border-radius: 8px;
    overflow: hidden;
    transition: transform 0.3s ease;
}

.card:hover {
    transform: translateY(-5px);
}
```

## 學習建議

1. **循序漸進**
   - 先掌握基本 HTML 結構
   - 學習基礎 CSS 樣式
   - 理解盒模型概念
   - 進階學習 Flexbox 和 Grid

2. **實踐練習**
   - 從簡單的頁面布局開始
   - 嘗試製作響應式設計
   - 練習常見的 UI 組件
   - 參考實際網站進行模仿

3. **開發工具**
   - 使用 VS Code 編輯器
   - 安裝 Live Server 擴展
   - 學會使用瀏覽器開發者工具
   - 使用 CSS Reset 或 Normalize.css

## 延伸資源

1. **線上學習平台**
   - [MDN Web Docs](https://developer.mozilla.org/)
   - [W3Schools](https://www.w3schools.com/)
   - [CSS-Tricks](https://css-tricks.com/)

2. **互動式學習**
   - [Flexbox Froggy](https://flexboxfroggy.com/)
   - [Grid Garden](https://cssgridgarden.com/)

3. **實用工具**
   - [Can I Use](https://caniuse.com/)
   - [CSS Generator](https://css3generator.com/)

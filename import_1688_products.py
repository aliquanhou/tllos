#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TLLOS Mall - 1688 Product Import Script
将1688采集的商品数据导入到TLLOS商城SQLite数据库
"""

import json
import sqlite3
import os
import sys
from datetime import datetime

# 配置
TLLOS_DB_PATH = r"C:\Users\Administrator\Doubao\chats\2026-09-04\new-chat\tllos\mall\data\mall.db"
DATA_DIR = r"D:\1688采集new-chat"

def get_or_create_category(conn, category_name):
    """获取或创建分类"""
    if not category_name:
        category_name = "其他"
    
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    
    # 创建分类
    cursor.execute(
        "INSERT INTO categories (name, parent_id, status, sort_order, created_at) VALUES (?, 0, 'active', 0, ?)",
        (category_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    return cursor.lastrowid

def get_or_create_brand(conn, brand_name):
    """获取或创建品牌"""
    if not brand_name:
        brand_name = "其他"
    
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM brands WHERE name = ?", (brand_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    
    # 创建品牌
    cursor.execute(
        "INSERT INTO brands (name, logo, description, status, sort_order, created_at) VALUES (?, '', '', 'active', 0, ?)",
        (brand_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )
    conn.commit()
    return cursor.lastrowid

def import_product_from_cleaned(conn, product):
    """从cleaned_1688.json格式导入商品"""
    title = product.get("title", product.get("original_title", "未命名商品"))
    sale_price = product.get("sale_price", 0)
    original_price = product.get("original_price", sale_price)
    main_images = product.get("main_images", [])
    detail_images = product.get("detail_images", [])
    skus = product.get("skus", [])
    category = product.get("category", {})
    company = product.get("company", {})
    
    # 获取分类ID
    category_name = category.get("name", "其他") if isinstance(category, dict) else str(category)
    category_id = get_or_create_category(conn, category_name)
    
    # 获取品牌ID
    brand_name = company.get("name", "其他") if isinstance(company, dict) else "其他"
    brand_id = get_or_create_brand(conn, brand_name)
    
    # 主图
    main_image = main_images[0] if main_images else ""
    images_json = json.dumps(main_images, ensure_ascii=False) if main_images else "[]"
    detail_images_json = json.dumps(detail_images, ensure_ascii=False) if detail_images else "[]"
    
    # 描述
    description = f"来源：1688 | 分类：{category_name} | 品牌：{brand_name}"
    detail = f"<p>商品详情</p><p>原价：¥{original_price}</p><p>促销价：¥{sale_price}</p>"
    
    # 库存
    stock = 100
    if skus:
        total_stock = sum(sku.get("stock", 0) for sku in skus if isinstance(sku, dict))
        if total_stock > 0:
            stock = total_stock
    
    # 检查商品是否已存在（通过标题）
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products WHERE name = ?", (title,))
    existing = cursor.fetchone()
    if existing:
        print(f"  [跳过] 商品已存在: {title[:30]}...")
        return existing[0]
    
    # 插入商品
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """INSERT INTO products 
           (name, category_id, brand_id, description, detail, main_image, images, price, stock, sales, status, sort_order, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'on', 0, ?, ?)""",
        (title, category_id, brand_id, description, detail, main_image, images_json, sale_price, stock, now, now)
    )
    product_id = cursor.lastrowid
    conn.commit()
    
    # 插入SKU
    if skus:
        for sku in skus:
            if isinstance(sku, dict):
                sku_code = sku.get("sku_code", sku.get("code", ""))
                spec = sku.get("spec", sku.get("name", ""))
                sku_price = sku.get("price", sale_price)
                sku_stock = sku.get("stock", 100)
                sku_image = sku.get("image", "")
                
                if isinstance(spec, dict):
                    spec = json.dumps(spec, ensure_ascii=False)
                elif isinstance(spec, list):
                    spec = json.dumps(spec, ensure_ascii=False)
                
                cursor.execute(
                    """INSERT INTO product_skus (product_id, sku_code, spec, price, stock, image, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (product_id, sku_code, str(spec), sku_price, sku_stock, sku_image, now)
                )
        conn.commit()
    
    print(f"  [成功] 导入商品: {title[:40]}... (ID: {product_id}, 价格: ¥{sale_price}, 库存: {stock})")
    return product_id

def import_product_from_batch(conn, product):
    """从batch_products.json格式导入商品"""
    title = product.get("title", "未命名商品")
    price = product.get("price", 0)
    original_price = product.get("original_price", price)
    images = product.get("images", [])
    detail_images = product.get("detail_images", [])
    skus = product.get("skus", [])
    attrs = product.get("attrs", {})
    category_name = product.get("category_name", "其他")
    brand_name = product.get("brand", "其他")
    
    # 获取分类ID和品牌ID
    category_id = get_or_create_category(conn, category_name)
    brand_id = get_or_create_brand(conn, brand_name)
    
    # 主图
    main_image = images[0] if images else ""
    images_json = json.dumps(images, ensure_ascii=False) if images else "[]"
    detail_images_json = json.dumps(detail_images, ensure_ascii=False) if detail_images else "[]"
    
    # 描述
    attr_str = ""
    if isinstance(attrs, dict):
        attr_str = " | ".join([f"{k}: {v}" for k, v in attrs.items()])
    description = f"来源：1688 | 分类：{category_name} | 品牌：{brand_name}"
    if attr_str:
        description += f" | 属性：{attr_str}"
    
    detail = f"<p>商品详情</p><p>原价：¥{original_price}</p><p>促销价：¥{price}</p>"
    
    # 库存
    stock = 100
    if skus:
        total_stock = sum(sku.get("stock", 0) for sku in skus if isinstance(sku, dict))
        if total_stock > 0:
            stock = total_stock
    
    # 检查商品是否已存在
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM products WHERE name = ?", (title,))
    existing = cursor.fetchone()
    if existing:
        print(f"  [跳过] 商品已存在: {title[:30]}...")
        return existing[0]
    
    # 插入商品
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """INSERT INTO products 
           (name, category_id, brand_id, description, detail, main_image, images, price, stock, sales, status, sort_order, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 'on', 0, ?, ?)""",
        (title, category_id, brand_id, description, detail, main_image, images_json, price, stock, now, now)
    )
    product_id = cursor.lastrowid
    conn.commit()
    
    # 插入SKU
    if skus:
        for sku in skus:
            if isinstance(sku, dict):
                sku_code = sku.get("sku_code", sku.get("code", ""))
                spec = sku.get("spec", sku.get("name", ""))
                sku_price = sku.get("price", price)
                sku_stock = sku.get("stock", 100)
                sku_image = sku.get("image", "")
                
                if isinstance(spec, (dict, list)):
                    spec = json.dumps(spec, ensure_ascii=False)
                
                cursor.execute(
                    """INSERT INTO product_skus (product_id, sku_code, spec, price, stock, image, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (product_id, sku_code, str(spec), sku_price, sku_stock, sku_image, now)
                )
        conn.commit()
    
    print(f"  [成功] 导入商品: {title[:40]}... (ID: {product_id}, 价格: ¥{price}, 库存: {stock})")
    return product_id

def main():
    print("=" * 60)
    print("TLLOS Mall - 1688商品导入脚本")
    print("=" * 60)
    
    # 检查数据库文件
    if not os.path.exists(TLLOS_DB_PATH):
        print(f"错误：数据库文件不存在: {TLLOS_DB_PATH}")
        print("请先启动TLLOS商城服务器以初始化数据库")
        return
    
    # 连接数据库
    conn = sqlite3.connect(TLLOS_DB_PATH)
    print(f"已连接数据库: {TLLOS_DB_PATH}")
    
    # 统计现有商品
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM products")
    existing_count = cursor.fetchone()[0]
    print(f"现有商品数量: {existing_count}")
    
    total_imported = 0
    total_skipped = 0
    
    # 1. 导入 cleaned_1688.json (59个商品)
    cleaned_path = os.path.join(DATA_DIR, "output", "cleaned_1688.json")
    if os.path.exists(cleaned_path):
        print(f"\n[1/2] 导入 cleaned_1688.json...")
        with open(cleaned_path, "r", encoding="utf-8") as f:
            products = json.load(f)
        print(f"找到 {len(products)} 个商品")
        
        for i, product in enumerate(products):
            print(f"  [{i+1}/{len(products)}]", end=" ")
            result = import_product_from_cleaned(conn, product)
            if result:
                # 检查是新导入还是已存在
                cursor.execute("SELECT created_at FROM products WHERE id = ?", (result,))
                created = cursor.fetchone()[0]
                if created and created.startswith(datetime.now().strftime("%Y-%m-%d")):
                    total_imported += 1
                else:
                    total_skipped += 1
    else:
        print(f"\n[跳过] 文件不存在: {cleaned_path}")
    
    # 2. 导入 batch_products.json (1个详细商品)
    batch_path = os.path.join(DATA_DIR, "v1.0", "batch_products.json")
    if os.path.exists(batch_path):
        print(f"\n[2/2] 导入 batch_products.json...")
        with open(batch_path, "r", encoding="utf-8") as f:
            products = json.load(f)
        print(f"找到 {len(products)} 个商品")
        
        for i, product in enumerate(products):
            print(f"  [{i+1}/{len(products)}]", end=" ")
            result = import_product_from_batch(conn, product)
            if result:
                cursor.execute("SELECT created_at FROM products WHERE id = ?", (result,))
                created = cursor.fetchone()[0]
                if created and created.startswith(datetime.now().strftime("%Y-%m-%d")):
                    total_imported += 1
                else:
                    total_skipped += 1
    else:
        print(f"\n[跳过] 文件不存在: {batch_path}")
    
    # 统计结果
    cursor.execute("SELECT COUNT(*) FROM products")
    final_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM product_skus")
    sku_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM categories")
    category_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM brands")
    brand_count = cursor.fetchone()[0]
    
    print("\n" + "=" * 60)
    print("导入完成！")
    print("=" * 60)
    print(f"  新导入商品: {total_imported}")
    print(f"  跳过已存在: {total_skipped}")
    print(f"  商品总数: {final_count}")
    print(f"  SKU总数: {sku_count}")
    print(f"  分类总数: {category_count}")
    print(f"  品牌总数: {brand_count}")
    print("=" * 60)
    
    conn.close()
    print("\n提示：请重启TLLOS商城服务器以加载新商品数据")

if __name__ == "__main__":
    main()

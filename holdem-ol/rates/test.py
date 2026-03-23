#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import struct
import sys
import os

# 扑克牌花色和点数的映射
SUITS = ['♠', '♥', '♣', '♦']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']

def uint8_to_card(uint8_val):
    """将 uint8 值转换为可读的扑克牌表示"""
    if uint8_val > 51:
        return f"未知牌({uint8_val})"
    
    rank_idx = uint8_val // 4
    suit_idx = uint8_val % 4
    
    return f"{SUITS[suit_idx]}{RANKS[rank_idx]}"

def decode_uint64(encoded, num_cards):
    """
    解码 uint64 值，提取牌和胜率
    参考 Go 代码中的 Decode 函数
    """
    cards = []
    for i in range(num_cards):
        # 从高位开始，每6位表示一张牌
        shift = 58 - 6 * i
        card_val = (encoded >> shift) & 0x3F
        cards.append(card_val)
    
    # 最低的 22 位表示胜率 (乘以 1,000,000)
    rate = encoded & 0x3FFFFF
    rate_float = rate / 1000000.0
    
    return cards, rate_float

def parse_rate_file(file_path, num_cards=None):
    """
    解析胜率文件，每8个字节为一个 uint64 值
    如果指定了 num_cards，则解析对应数量的牌
    否则尝试根据文件名猜测牌的数量
    """
    # 尝试从文件名猜测牌的数量
    if num_cards is None:
        dir_name = os.path.basename(os.path.dirname(file_path))
        if dir_name.startswith('board'):
            num_cards = int(dir_name[5:])
        else:
            # 默认为2张牌（手牌）
            num_cards = 2
    
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            
        # 检查文件大小是否为8的倍数
        if len(data) % 8 != 0:
            print(f"警告: 文件大小 {len(data)} 不是8的倍数")
            
        # 每8个字节解析一个 uint64
        for i in range(0, len(data), 8):
            if i + 8 > len(data):
                break
                
            # 使用 struct 模块解析 uint64 (大端序)
            encoded = struct.unpack('>Q', data[i:i+8])[0]
            
            # 解码牌和胜率
            cards, rate = decode_uint64(encoded, num_cards)
            
            # 转换为可读的牌表示
            card_strs = [uint8_to_card(c) for c in cards]
            
            # 打印结果
            print(f"牌: {' '.join(card_strs)}, 胜率: {rate:.6f}")
            
    except Exception as e:
        print(f"解析文件时出错: {e}")
        return False
        
    return True

def main():
    file_path = './holdem/board0/'
    num_cards = 2

    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在")
        return
        
    parse_rate_file(file_path, num_cards)

if __name__ == "__main__":
    main()

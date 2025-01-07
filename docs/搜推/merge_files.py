import os
import re

def natural_sort_key(s):
    # 从文件名中提取数字并转换为整数，用于自然排序
    match = re.search(r'image-(\d+)\.txt$', s)
    if match:
        return int(match.group(1))
    return float('inf')  # 将非匹配的文件排到最后

def merge_txt_files(directory, output_file):
    # 获取目录下所有符合 image-数字.txt 格式的文件
    txt_files = [f for f in os.listdir(directory) 
                if re.match(r'image-\d+\.txt$', f)]
    
    # 按文件名中的数字排序
    txt_files.sort(key=natural_sort_key)
    
    # 创建输出文件
    with open(os.path.join(directory, output_file), 'w', encoding='utf-8') as outfile:
        outfile.write("=== 搜推系统内容整合 ===\n")
        outfile.write(f"创建时间：{os.popen('date "+%Y-%m-%d"').read().strip()}\n\n")
        
        # 遍历每个文件并写入内容
        for filename in txt_files:
            if filename == output_file:
                continue
                
            outfile.write(f"\n=== Content of {filename} ===\n")
            try:
                with open(os.path.join(directory, filename), 'r', encoding='utf-8') as infile:
                    content = infile.read().strip()
                    outfile.write(content + "\n")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

if __name__ == "__main__":
    # 设置目录和输出文件名
    directory = os.path.dirname(os.path.abspath(__file__))
    output_file = "搜推系统内容整合_自动生成.txt"
    
    # 执行合并
    merge_txt_files(directory, output_file)
    print(f"Files merged successfully into {output_file}")
    # 打印处理的文件列表
    txt_files = [f for f in os.listdir(directory) if re.match(r'image-\d+\.txt$', f)]
    txt_files.sort(key=natural_sort_key)
    print("\nProcessed files in order:")
    for f in txt_files:
        print(f)

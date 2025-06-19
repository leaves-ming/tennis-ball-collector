import os
import time
import sys  # 新增：导入sys模块

# 新增：将项目根目录添加到模块搜索路径（假设src目录与src-3目录同级）
# __file__ 获取当前文件路径，os.path.dirname 逐级向上获取父目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

if os.path.exists('process.py'):
    from process import process_img
else:
    from src.process import process_img  # 现在可以正确找到src模块


def run():
    imgs_folder = './test_imgs/'
    img_paths = os.listdir(imgs_folder)
    def now():
        return time.time()*1000
    last_time = 0
    count_time = 0
    max_time = 0
    min_time = now()

    d={}
    for img_path in img_paths:
        if not (img_path.endswith('.jpg') or img_path.endswith('.png')):
            continue
        print(img_path,':')

        last_time = now()
        user_result = process_img(imgs_folder+img_path) #, processed_frame
        run_time = now() - last_time
        print('user result:\n',user_result)

        print('run time: ', run_time, 'ms')

        print()
        count_time += run_time
        if run_time > max_time:
            max_time = run_time
        if run_time < min_time:
            min_time = run_time
        d[img_path]={'re':user_result,'t':run_time}
    print('\n')
    print('avg time: ','%.2f'%(count_time/len(img_paths)),'ms')
    print('max time: ','%.2f'%max_time,'ms')
    print('min time: ','%.2f'%min_time,'ms')

    d['avg_time']='%.2f'%(count_time/len(img_paths))
    d['max_time']='%.2f'%max_time
    d['min_time']='%.2f'%min_time
    f=open('results.txt','wb')
    f.write(str(d).encode('UTF-8'))
    f.close()
if __name__=='__main__':
    run()

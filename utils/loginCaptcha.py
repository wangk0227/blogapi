import os, random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

path = Path(__file__).parent.parent


def randomtxt():
    '''随机的验证码'''
    txt_list = []
    txt_list.extend([i for i in range(65, 91)])
    txt_list.extend([i for i in range(97, 123)])
    txt_list.extend([i for i in range(48, 58)])
    return chr(txt_list[random.randint(0, len(txt_list) - 1)])


def txtcolor():
    '''随机的字体颜色'''
    return random.randint(32, 127), random.randint(32, 127), random.randint(32, 127)


def generatecode():
    width = 200
    height = 60
    code_num = ''

    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    for w in range(width):
        for h in range(height):
            draw.point((w, h), fill=(255, 255, 255))
    myfont = ImageFont.truetype('arial.ttf', 36)
    for i in range(4):
        text = randomtxt()
        code_num += text
        draw.text((50 * i + 10, 10), text, font=myfont, fill=txtcolor())

    code_name = 'media\\login_captcha\\%s.png' % code_num
    image_name = os.path.join(path, code_name)
    with open(image_name, 'wb') as fp:
        image.save(fp, 'PNG')
    return code_num, code_name

from paddleocr import PaddleOCR

def ocr(img_path,lang="ch"):
    ocr = PaddleOCR(use_angle_cls=True, lang=lang)  # need to run only once to download and load model into memory
    result = ocr.ocr(img_path, cls=True)
    result = result[0]
    txts = [line[1][0] for line in result]
    return "\n".join(txts)
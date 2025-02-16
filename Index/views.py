from django.shortcuts import render

# Create your views here.
import os
import cv2
import numpy as np
import pytesseract
from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from PlakaTanima import settings
# Tesseract'ın doğru yolu
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def index(request):
    if request.method == 'POST' and request.FILES.get('myFile'):
        image = request.FILES['myFile']
        fs = FileSystemStorage()
        filename = fs.save(os.path.join(settings.BASE_DIR, 'Index', 'static', 'img', 'cars', image.name), image)
        uploaded_file_url = fs.url(filename)
        img_name = image.name
        try:
            img = cv2.imread(fs.path(filename))
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blur, 75, 200)

            contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

            plate = None
            for c in contours:
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                if len(approx) == 4:
                    plate = approx
                    break

            if plate is not None:
                mask = np.zeros(gray.shape, np.uint8)
                new_image = cv2.drawContours(mask, [plate], 0, 255, -1)
                new_image = cv2.bitwise_and(img, img, mask=mask)
                (x, y) = np.where(mask == 255)
                (topx, topy) = (np.min(x), np.min(y))
                (bottomx, bottomy) = (np.max(x), np.max(y))
                cropped = gray[topx:bottomx+1, topy:bottomy+1]
                text = pytesseract.image_to_string(cropped, config='--psm 11')
            else:
                text = "Plaka bulunamadı"
            return render(request, 'index.html', {'text': text, 'uploaded_file_url': img_name})
        except:
            text = "Sorun Oluştu!"
            return render(request, 'index.html', {'text': text, 'uploaded_file_url': img_name})
    elif request.method == 'POST':
        # Kullanıcı dosya yüklemediği zaman hata mesajı göster
        error_message = "Lütfen bir dosya seçin!"
        return render(request, 'index.html', {'error_message': error_message})

    return render(request, 'index.html')

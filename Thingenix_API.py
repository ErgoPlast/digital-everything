import re

def sense_T(data): #
    sT_data= re.compile(r"(04)(0400)(\d{2})([0-9A-Z]{4})")
    sT_port = sT_data.findall(data)[0][0] # порт датчика
    sT_type = sT_data.findall(data)[0][1] # тип датчика  ( числовой идентификатор)
    sT_byte_amount = sT_data.findall(data)[0][2] # количество байт на данные
    sT_temp = sT_data.findall(data)[0][3] # данные температурного датчика
    sT_temp = bytes.fromhex(sT_temp)
    sT_temp = int.from_bytes(sT_temp, byteorder='big', signed=True)
    sT_temp = sT_temp / 100
    return sT_temp

def sense_V(data):
    sV_data = re.compile(r"(02)(0200)([0-9A-Z]{2})([0-9A-Z]{26})")
    sV_span_X = sV_data.findall(data)[0][3][2:4] + sV_data.findall(data)[0][3][0:2]  # размах ускорения по оси X
    sV_span_Y = sV_data.findall(data)[0][3][6:8] + sV_data.findall(data)[0][3][4:6]
    sV_span_Z = sV_data.findall(data)[0][3][10:12] + sV_data.findall(data)[0][3][8:10]
    sV_sigma_X = sV_data.findall(data)[0][3][14:16] + sV_data.findall(data)[0][3][12:14]
    sV_sigma_Y = sV_data.findall(data)[0][3][18:20] + sV_data.findall(data)[0][3][16:18]
    sV_sigma_Z = sV_data.findall(data)[0][3][22:24] + sV_data.findall(data)[0][3][20:22]
    sV_freq = sV_data.findall(data)[0][3][24:26]

    #перевод данных в 10-ную систему
    sV_span_X = int(sV_span_X, 16) / 100
    sV_span_Y = int(sV_span_Y, 16) / 100
    sV_span_Z = int(sV_span_Z, 16) / 100
    sV_sigma_X = int(sV_sigma_X, 16) / 100
    sV_sigma_Y = int(sV_sigma_Y, 16) / 100
    sV_sigma_Z = int(sV_sigma_Z, 16) / 100
    sV_freq = int(sV_freq, 16)

    spisok =[sV_span_X, sV_span_Y, sV_span_Z, sV_sigma_X, sV_sigma_Y, sV_sigma_Z, sV_freq]

    return spisok

print(sense_T('2377326498349800466304040002F9344'))

sense_V('2377326498349800202000DE904BA04BC040802A4017102198490FA833')
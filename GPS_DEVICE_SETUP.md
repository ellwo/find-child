# إعداد أجهزة GPS الجديدة

## للإعداد السريع لجهاز GPS جديد:

### الخطوات المطلوبة:

1. **في ملف `gps-esp.ino` - تعديل `device_id` فقط**:
   ```cpp
   const char* device_id = "GPS_TRACKER_002";  // ⚠️ غيّر هذا لكل جهاز جديد
   ```

2. **في لوحة الإدارة - إنشاء GPS Tracker جديد**:
   - اذهب إلى: **Admin Panel → Trackers → Create Tracker**
   - أدخل نفس `device_id` الذي استخدمته في الكود
   - مثال: إذا استخدمت `GPS_TRACKER_002` في الكود، استخدم نفس القيمة هنا

### الإعدادات المشتركة (لا تحتاج تغيير):

✅ **api_url**: `https://safe-trip.nabaai.com/api/device/gps/update`  
✅ **api_key**: `changeme_gps_api_key` (نفسها لجميع الأجهزة)

### الإعدادات التي قد تحتاج تغيير:

⚠️ **ssid** و **password**: قد تكون مختلفة حسب موقع الجهاز
- إذا كان الجهاز في نفس موقع WiFi، استخدم نفس الإعدادات
- إذا كان في موقع مختلف، غيّر `ssid` و `password`

### مثال: إعداد 3 أجهزة GPS

**الجهاز 1** (`gps-esp.ino`):
```cpp
const char* device_id = "GPS_TRACKER_001";
```

**الجهاز 2** (`gps-esp.ino`):
```cpp
const char* device_id = "GPS_TRACKER_002";
```

**الجهاز 3** (`gps-esp.ino`):
```cpp
const char* device_id = "GPS_TRACKER_003";
```

### في لوحة الإدارة:

أنشئ 3 GPS Trackers:
- Tracker 1: `device_id = "GPS_TRACKER_001"`
- Tracker 2: `device_id = "GPS_TRACKER_002"`
- Tracker 3: `device_id = "GPS_TRACKER_003"`

### ملاحظات مهمة:

1. ⚠️ **`device_id` يجب أن يكون فريداً** لكل جهاز
2. ⚠️ **`device_id` في الكود يجب أن يطابق `device_id` في قاعدة البيانات**
3. ✅ باقي الإعدادات (`api_url`, `api_key`) نفسها لجميع الأجهزة
4. ✅ يمكنك استخدام أي اسم لـ `device_id` (مثلاً: `BUS_1_GPS`, `TRACKER_ALPHA`, إلخ)

### خطوات سريعة:

1. افتح `gps-esp.ino` في Arduino IDE
2. غيّر `device_id` إلى قيمة فريدة
3. ارفع الكود للجهاز
4. أنشئ GPS Tracker في لوحة الإدارة بنفس `device_id`
5. ربط GPS Tracker بالباص (اختياري)

**جاهز!** 🎉



## للإعداد السريع لجهاز GPS جديد:

### الخطوات المطلوبة:

1. **في ملف `gps-esp.ino` - تعديل `device_id` فقط**:
   ```cpp
   const char* device_id = "GPS_TRACKER_002";  // ⚠️ غيّر هذا لكل جهاز جديد
   ```

2. **في لوحة الإدارة - إنشاء GPS Tracker جديد**:
   - اذهب إلى: **Admin Panel → Trackers → Create Tracker**
   - أدخل نفس `device_id` الذي استخدمته في الكود
   - مثال: إذا استخدمت `GPS_TRACKER_002` في الكود، استخدم نفس القيمة هنا

### الإعدادات المشتركة (لا تحتاج تغيير):

✅ **api_url**: `https://safe-trip.nabaai.com/api/device/gps/update`  
✅ **api_key**: `changeme_gps_api_key` (نفسها لجميع الأجهزة)

### الإعدادات التي قد تحتاج تغيير:

⚠️ **ssid** و **password**: قد تكون مختلفة حسب موقع الجهاز
- إذا كان الجهاز في نفس موقع WiFi، استخدم نفس الإعدادات
- إذا كان في موقع مختلف، غيّر `ssid` و `password`

### مثال: إعداد 3 أجهزة GPS

**الجهاز 1** (`gps-esp.ino`):
```cpp
const char* device_id = "GPS_TRACKER_001";
```

**الجهاز 2** (`gps-esp.ino`):
```cpp
const char* device_id = "GPS_TRACKER_002";
```

**الجهاز 3** (`gps-esp.ino`):
```cpp
const char* device_id = "GPS_TRACKER_003";
```

### في لوحة الإدارة:

أنشئ 3 GPS Trackers:
- Tracker 1: `device_id = "GPS_TRACKER_001"`
- Tracker 2: `device_id = "GPS_TRACKER_002"`
- Tracker 3: `device_id = "GPS_TRACKER_003"`

### ملاحظات مهمة:

1. ⚠️ **`device_id` يجب أن يكون فريداً** لكل جهاز
2. ⚠️ **`device_id` في الكود يجب أن يطابق `device_id` في قاعدة البيانات**
3. ✅ باقي الإعدادات (`api_url`, `api_key`) نفسها لجميع الأجهزة
4. ✅ يمكنك استخدام أي اسم لـ `device_id` (مثلاً: `BUS_1_GPS`, `TRACKER_ALPHA`, إلخ)

### خطوات سريعة:

1. افتح `gps-esp.ino` في Arduino IDE
2. غيّر `device_id` إلى قيمة فريدة
3. ارفع الكود للجهاز
4. أنشئ GPS Tracker في لوحة الإدارة بنفس `device_id`
5. ربط GPS Tracker بالباص (اختياري)

**جاهز!** 🎉


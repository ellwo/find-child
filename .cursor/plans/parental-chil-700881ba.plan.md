<!-- 700881ba-16b7-46c4-8d94-7d81da72f026 65b5fcfb-a129-4109-b487-b78814edf354 -->
# خطة تحسين نظام التحضير

## المتطلبات الرئيسية

1. **نسبة التشابه**: تغيير الحد الأدنى من 0.7 (70%) إلى 0.9 (90%) مع إمكانية التعديل من Settings
2. **حفظ وعرض الصورة**: التأكد من حفظ الصورة وعرضها في تفاصيل التحضير
3. **منطق التحديث**: إذا كان التحضير السابق بنسبة أعلى، لا يتم تحديثه
4. **عدد التحضيرات**: السماح بتحضيرين في اليوم الواحد (قابل للتعديل من Settings)
5. **شاشة Admin**: إضافة شاشة مشابهة لشاشة الأب لتتبع أي طالب مع إمكانية الفرز
6. **Background Worker**: تحويل معالجة الصور إلى worker service منفصل

## التغييرات المطلوبة

### 1. تحديث SystemSettings Model

**الملف**: `api/app/models.py`

- إضافة حقل `attendance_similarity_threshold` (Float, default=0.9)
- إضافة حقل `max_daily_attendances` (Integer, default=2)

### 2. تحديث Schemas

**الملف**: `api/app/schemas.py`

- تحديث `SystemSettingsBase` و `SystemSettingsResponse` لإضافة الحقول الجديدة
- تحديث `AttendanceResponse` للتأكد من تضمين `detected_image_path` و `image_url`

### 3. تحديث منطق Face Recognition

**الملف**: `api/app/services/face_recognition.py`

- تعديل `identify_student_from_face` لقراءة `attendance_similarity_threshold` من Settings بدلاً من القيمة الثابتة 0.7
- تحديث `record_attendance`:
- التحقق من عدد التحضيرات في اليوم (من Settings)
- التحقق من نسبة التشابه قبل التحديث (إذا كان التحضير السابق بنسبة أعلى، لا يتم التحديث)
- التحقق من أن نسبة التشابه >= threshold من Settings

### 4. تحديث Admin Settings Page

**الملف**: `aimirror-vision/src/pages/admin/Settings.tsx`

- إضافة حقل `attendance_similarity_threshold` (نسبة التشابه المطلوبة)
- إضافة حقل `max_daily_attendances` (عدد التحضيرات المسموح في اليوم)

### 5. إنشاء Admin Student Tracking Page

**الملف الجديد**: `aimirror-vision/src/pages/admin/StudentTracking.tsx`

- نسخ الكود من `aimirror-vision/src/pages/parent/StudentTracking.tsx`
- تعديل API calls لاستخدام admin endpoints
- إضافة فلاتر للفرز (بالتاريخ، بالباص، بالطالب)
- إضافة dropdown لاختيار الطالب

### 6. إنشاء Admin API Endpoints

**الملف**: `api/app/routers/admin.py`

- إضافة `GET /api/admin/students/{student_id}/tracking` - معلومات الطالب مع الحضور
- إضافة `GET /api/admin/students/{student_id}/attendance/history` - سجل الحضور مع فلاتر
- إضافة `GET /api/admin/students` - قائمة جميع الطلاب (لاختيار الطالب في الصفحة)

### 7. إنشاء Background Worker Service

**الملفات الجديدة**:

- `api/app/workers/__init__.py`
- `api/app/workers/image_processor.py` - معالجة الصور في background
- `api/app/worker_main.py` - نقطة دخول Worker
- `api/worker_requirements.txt` - dependencies للـ worker (Celery, Redis)

**التعديلات**:

- `api/app/main.py`: تعديل `/api/upload_camera_face` ليقبل الصورة ويضعها في queue بدلاً من المعالجة المباشرة
- `docker-compose.yml`: إضافة services:
- `redis` - للـ message queue
- `worker` - Celery worker service

### 8. تحديث CRUD Functions

**الملف**: `api/app/crud.py`

- تحديث `get_attendance_history` لدعم فلاتر إضافية (bus_id, student_id)
- إضافة دالة `get_attendances_today_by_student` للتحقق من عدد التحضيرات في اليوم

### 9. تحديث API Client

**الملف**: `aimirror-vision/src/lib/api.ts`

- إضافة `getStudentTracking(id)` - للـ admin
- إضافة `getStudentAttendanceHistory(id, filters)` - للـ admin مع فلاتر

### 10. تحديث Routing

**الملف**: `aimirror-vision/src/App.tsx`

- إضافة route `/admin/students/:id/tracking` للـ admin student tracking

## تفاصيل التنفيذ

### Background Worker Architecture

- استخدام Celery مع Redis كـ message broker
- إنشاء task `process_camera_image` في `api/app/workers/image_processor.py`
- الـ task يقوم بـ:

        1. Face detection (باستخدام Detection Service)
        2. Face recognition (باستخدام Recognition Service)
        3. Attendance recording (مع التحقق من الشروط الجديدة)
        4. WebSocket broadcasting للـ admin والـ parents

### منطق التحضير الجديد

**في `record_attendance`:**

1. قراءة `attendance_similarity_threshold` و `max_daily_attendances` من Settings
2. التحقق من أن `similarity_score >= attendance_similarity_threshold` (افتراضي 0.9)
3. التحقق من عدد التحضيرات في اليوم الحالي للطالب:

            - إذا وصل للحد الأقصى (`max_daily_attendances`)، لا يتم إنشاء تحضير جديد
            - إذا كان هناك تحضير سابق في نفس اليوم:
                    - إذا كان `similarity_score` الجديد > السابق، يتم تحديث التحضير السابق
                    - إذا كان `similarity_score` السابق >= الجديد، لا يتم التحديث

4. حفظ الصورة في `detected_image_path` (موجود بالفعل)
5. عرض الصورة في API response عبر `image_url`

### Background Worker Implementation

**الملف**: `api/app/workers/image_processor.py`

```python
from celery import Celery
from app.db import SessionLocal
from app.services import face_recognition
# ... imports أخرى

celery_app = Celery('image_processor', broker='redis://redis:6379/0')

@celery_app.task
def process_camera_image(image_path: str, camera_id: str, camera_name: str, timestamp: datetime):
    """Process camera image in background."""
    db = SessionLocal()
    try:
        # 1. Face detection
        # 2. Face recognition
        # 3. Attendance recording
        # 4. WebSocket broadcast
    finally:
        db.close()
```

**الملف**: `api/app/worker_main.py`

```python
from app.workers.image_processor import celery_app

if __name__ == '__main__':
    celery_app.start()
```

**الملف**: `api/worker_requirements.txt`

```
celery==5.3.4
redis==5.0.1
```

**التعديل في `api/app/main.py`:**

- تعديل `/api/upload_camera_face` ليقبل الصورة ويحفظها فقط
- إضافة task إلى Celery queue بدلاً من المعالجة المباشرة
- إرجاع response فوري مع status "processing"

### Docker Compose Updates

**إضافة services:**

```yaml
redis:
  image: redis:7-alpine
  container_name: find-child-redis
  networks:
 - faces_network

worker:
  build:
    context: ./api
    dockerfile: Dockerfile.worker
  container_name: find-child-worker
  depends_on:
 - redis
 - postgres
  environment:
 - DATABASE_URL=${DATABASE_URL}
 - REDIS_URL=redis://redis:6379/0
  volumes:
 - storage_data:/data/storage
  networks:
 - faces_network
```

### Admin Student Tracking Page

**الميزات:**

1. Dropdown لاختيار الطالب (من قائمة جميع الطلاب)
2. عرض معلومات الطالب (اسم، باص، ولي أمر)
3. عرض آخر تحضير مع الصورة
4. عرض سجل التحضيرات مع فلاتر:

            - فلتر بالتاريخ (start_date, end_date)
            - فلتر بالباص (bus_id)
            - فلتر بالطالب (student_id - للبحث)

5. عرض موقع الحافلة على الخريطة
6. WebSocket للـ real-time tracking

### API Endpoints الجديدة

**في `api/app/routers/admin.py`:**

1. `GET /api/admin/students/{student_id}/tracking`

            - معلومات الطالب الكاملة
            - آخر تحضير
            - معلومات الحافلة
            - موقع GPS الحالي

2. `GET /api/admin/students/{student_id}/attendance/history`

            - سجل التحضيرات مع فلاتر:
                    - `start_date`, `end_date`
                    - `bus_id`
                    - `skip`, `limit`
            - ترتيب حسب `detected_at` descending

3. `GET /api/admin/students` (موجود بالفعل، قد يحتاج تحسين)

### تحديث AttendanceResponse Schema

**في `api/app/schemas.py`:**

- التأكد من تضمين `detected_image_path`
- إضافة `image_url` (computed field) لعرض الصورة

### تحديث init_data.py

**في `api/app/init_data.py`:**

- إضافة القيم الافتراضية الجديدة:
        - `attendance_similarity_threshold = 0.9`
        - `max_daily_attendances = 2`

## خطوات التنفيذ بالترتيب

1. تحديث Models و Schemas (SystemSettings)
2. تحديث منطق Face Recognition (record_attendance)
3. إنشاء Background Worker Service
4. تحديث upload_camera_face endpoint
5. تحديث Admin Settings Page
6. إنشاء Admin Student Tracking Page
7. إضافة Admin API Endpoints
8. تحديث Routing
9. تحديث Docker Compose
10. اختبار شامل

## ملاحظات مهمة

- يجب التأكد من أن الصور المحفوظة في `detected_image_path` قابلة للوصول عبر `/storage/faces/...`
- Worker service يجب أن يكون قادراً على الوصول إلى نفس قاعدة البيانات و CompreFace
- WebSocket broadcasting يجب أن يعمل من Worker أيضاً
- يجب إضافة error handling و retry logic في Worker tasks
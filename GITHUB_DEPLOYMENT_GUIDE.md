# 🚀 คู่มือการนำขึ้น GitHub & เปิดใช้งาน GitHub Pages

> ขั้นตอนการอัปโหลดโค้ดและเอกสารขึ้น GitHub เพื่อเปิดหน้าเว็บไซต์สอน AIoT ตามโจทย์ใบงาน

---

## ขั้นตอนที่ 1: ตรวจสอบหน้าเว็บเอกสารในเครื่อง (Local Preview)

คุณสามารถเปิดดูหน้าเว็บเอกสารบทเรียนในเครื่องของคุณก่อนขึ้น GitHub ได้โดยเปิด Terminal แล้วพิมพ์:

```bash
cd D:\TSE34\CN466\Project_Final
py -m mkdocs serve
```

เปิดเบราว์เซอร์ไปที่: [http://127.0.0.1:8000](http://127.0.0.1:8000) จะเห็นเว็บไซต์สอน AIoT สวยงามเหมือนเว็บของ อ.ศุภชัย ทันที! (กด `Ctrl + C` เพื่อหยุดเมื่อดูเสร็จ)

---

## ขั้นตอนที่ 2: สร้าง Repository ใหม่บน GitHub

1. เข้าไปที่ [GitHub](https://github.com) แล้วล็อกอินเข้าบัญชีของคุณ
2. คลิกปุ่ม **New** (สร้าง Repository ใหม่)
3. ตั้งชื่อ Repository เช่น: `aiot-coldchain-monitor` หรือ `CN466-Project-AIoT`
4. ตั้งค่าเป็น **Public** (เพื่อให้เปิด GitHub Pages ฟรีได้)
5. **ไม่ต้องติ๊ก** Add a README file (เพราะในโปรเจกต์เรามีไฟล์พร้อมอยู่แล้ว)
6. คลิก **Create repository**

---

## ขั้นตอนที่ 3: สั่ง Push โค้ดขึ้น GitHub

เปิด Terminal ในโฟลเดอร์โปรเจกต์ `D:\TSE34\CN466\Project_Final` แล้วรันคำสั่งตามลำดับ:

```bash
cd D:\TSE34\CN466\Project_Final

# 1. เริ่มต้น Git
git init

# 2. เพิ่มไฟล์ทั้งหมดเข้าสู่การติดตาม
git add .

# 3. บันทึก Commit แรก
git commit -m "feat: complete AIoT industrial cold chain project and docs"

# 4. ตั้งชื่อ Branch หลักเป็น main
git branch -M main

# 5. เชื่อมต่อกับ Repository ของคุณบน GitHub (เปลี่ยน YOUR_USERNAME และ REPO_NAME)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# 6. Push ข้อมูลขึ้นสู่ GitHub
git push -u origin main
```

---

## ขั้นตอนที่ 4: เปิดใช้งาน GitHub Pages

เมื่อ Push โค้ดเสร็จแล้ว:
1. ไปที่หน้า Repository บน GitHub -> คลิกแท็บ **Settings**
2. เมนูด้านซ้ายเลือกหัวข้อ **Pages**
3. ที่หัวข้อ **Build and deployment**:
   - ช่อง **Source** ให้เลือกเป็น: **GitHub Actions**
4. ระบบจะทำการ Build และ Deploy เว็บไซต์ให้อัตโนมัติ (ใช้เวลาประมาณ 1 นาที)
5. เมื่อเสร็จแล้ว จะได้รับ URL ของเว็บไซต์ เช่น:  
   👉 `https://YOUR_USERNAME.github.io/YOUR_REPO_NAME/`

นำ URL นี้ไปกรอกส่งในระบบส่งงานของอาจารย์ได้เลยครับ! 🎉

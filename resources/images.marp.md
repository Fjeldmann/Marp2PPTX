---
marp: true
paginate: true
---
# Regular background image
![bg](https://picsum.photos/1200/1200?image=12)


---
# Regular background image with opacity
![bg opacity:.2](https://picsum.photos/1200/1200?image=12)

---

# Regular background image with grayscale filter
![bg grayscale](https://picsum.photos/1200/1200?image=12)

---
# Three vertical bg images
Text will be shown above the midlle image

![bg vertical](https://picsum.photos/1200/1200/?image=99)
![bg](https://picsum.photos/1200/1200/?image=100)
![bg](https://picsum.photos/1200/1200/?image=102)

<!-- These images will arrange in a horizontal row. -->

---

# Three horizontal bg images

![bg horizontal](https://picsum.photos/1200/1200/?image=99)
![bg](https://picsum.photos/1200/1200/?image=100)
![bg](https://picsum.photos/1200/1200/?image=102)

<!-- You may change alignment direction from horizontal to vertical, by using vertical direction keyword. -->

---

![bg left](https://picsum.photos/720?image=29)

# Split backgrounds

The space of a slide content will shrink to the right side.


---
<!-- header: ![img](https://picsum.photos/25/25?image=1)  -->

![bg right](https://picsum.photos/720?image=3)
![bg](https://picsum.photos/720?image=20)

# Split + Multiple BGs

The space of a slide content will shrink to the left side.

---

![bg left:33%](https://picsum.photos/720?image=27)

# Split backgrounds with specified size


---

![bg right:33%](https://picsum.photos/720?image=27)

# Split backgrounds with specified size


--- 


![bg left:38% 70%](https://picsum.photos/595/595?image=27)

# Split backgrounds with specified size and position

---


![bg cover](https://picsum.photos/1920/500?image=12)

# Background size: cover
<!-- Scale image to fill the slide. (Default) -->

---

![bg contain](https://picsum.photos/1920/500?image=12)

# Background size: contain

---

![bg fit](https://picsum.photos/500/500?image=12)

# Background size: fit
<!-- Scale image to fit within the slide. -->

---

![bg auto](https://picsum.photos/500/500?image=12)
# Background size: auto

---


![bg 50%](https://picsum.photos/500/500?image=12)

# Background size: 50%
<!-- Scale image to 50% of the slide size. -->


---

<!-- Resizing image
You can resize image by using width and height keyword options.

![width:200px](image.jpg) Setting width to 200px 
![height:30cm](image.jpg) Setting height to 300px 
![width:200px height:30cm](image.jpg) Setting both lengths 
Copy to clipboardErrorCopied
We also support the shorthand options w and h. Normally it’s useful to use these.

![w:32 h:32](image.jpg) Setting size to 32x32 px
Copy to clipboardErrorCopied
Inline images only allow auto keyword and the length units defined in CSS. -->

![bg w:90%](https://picsum.photos/1200/1200?image=100)

# Background size: 90% width shorthand

---

![bg h:90%](https://picsum.photos/1200/1200?image=100)

# Background size: 90% height shorthand

---

![bg width:90%](https://picsum.photos/1200/1200?image=100)

# Background size: 90% width

---

![bg height:90%](https://picsum.photos/1200/1200?image=100)


# Background size: 90% height


---

![bg horizontal width:200px](https://picsum.photos/1200/896?image=100)
![bg width:150px](https://picsum.photos/1200/896?image=100)
![bg w:100px](https://picsum.photos/1200/896?image=100)
![bg height:50px](https://picsum.photos/1200/896?image=100)
![bg h:25px](https://picsum.photos/1200/896?image=100)

# Multiple background images with specified size

---

<style>
    .image-wrap-0 { width:400px; height:400px;  border-radius: 0%; overflow:hidden}
</style>

# rounded corner cropped photo with 0% border radius 

<div class="image-wrap-0">
    <img  src="https://picsum.photos/500/500?image=95" alt="Forest" />
</div>

---


<style>
    .image-wrap-10 { width:400px; height:400px;  border-radius: 10%; overflow:hidden}
</style>

# rounded corner cropped photo with 10% border radius

<div class="image-wrap-10">
    <img  src="https://picsum.photos/500/500?image=95" alt="Forest" />
</div>

---


<style>
    .image-wrap-35 { width:400px; height:400px;  border-radius: 35%; overflow:hidden}
</style>

# rounded corner cropped photo with 35% border radius

<div class="image-wrap-35">
    <img  src="https://picsum.photos/500/500?image=95" alt="Forest" />
</div>

---


<style>
    .image-wrap-45 { width:400px; height:400px;  border-radius: 45%; overflow:hidden}
</style>

# rounded corner cropped photo with 45% border radius

<div class="image-wrap-45">
    <img  src="https://picsum.photos/500/500?image=95" alt="Forest" />
</div>


---


<style>
    .image-wrap-50 { width:400px; height:400px;  border-radius: 50%; overflow:hidden}
</style>

# rounded corner cropped photo with 50% border radius

<div class="image-wrap-50">
    <img  src="https://picsum.photos/500/500?image=95" alt="Forest" />
</div>

--- 

# reuse style - should be identical to the one above

<div class="image-wrap-50">
    <img  src="https://picsum.photos/500/500?image=95" alt="Forest" />
</div>

---


<style>
.image-wrap-circle { width:400px; height:400px;  border-radius: 50%; overflow:hidden}
.image {opacity: 0.1; width:90%; height:90%; object-fit: cover; object-position: 0px 50px; transform: scale(1.5); }
</style>

# two classes - one for the wrapper and one for the image - to achieve a circular cropped photo with zoom and custom position

<div class="image-wrap-circle">
    <img class="image" src="https://picsum.photos/1200/1200?image=95" alt="Forest" />
</div>

---


<style>
.image-wrap-circle-2 { width:400px; height:400px;  border-radius: 50%; overflow:hidden; box-shadow: 5px 0px 10px rgba(0,0,0,0.5); }
.image-2 {width:90%; height:90%; object-fit: cover; object-position: 0px 50px; transform: scale(1.5); filter:  }
</style>

# two classes - one for the wrapper and one for the image - to achieve a circular cropped photo with zoom and custom position

<div class="image-wrap-circle-2">
    <img class="image-2" src="https://picsum.photos/1200/1200?image=95" alt="Forest" />
</div>

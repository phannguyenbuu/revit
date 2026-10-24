import os
import ezdxf

template_path = os.path.join(os.path.dirname(__file__), "templates", "dim.dxf")
doc = ezdxf.readfile(template_path)
msp = doc.modelspace()

# Ensure standard style has tahoma.ttf
std = doc.styles.get('Standard')
print("Standard style font:", std.dxf.font)

# Add Vietnamese text
msp.add_text("DẦM CHÍNH ĐÀ KIỀNG CỘT - KIỂM TRA FONT TIẾNG VIỆT", dxfattribs={
    'height': 300,
    'style': 'Standard'
})

doc.saveas('test_vietnamese_font.dxf')
print("Successfully saved test_vietnamese_font.dxf")

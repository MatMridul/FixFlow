import os
import sys

try:
    import comtypes.client
except ImportError:
    try:
        import win32com.client as win32
    except ImportError:
        print("No COM client library, PPTX preserved as primary format.")
        sys.exit(0)

pairs = [
    ("SRM_Claude's Plan_02.pptx", "SRM_Claude's Plan_02.pdf"),
    ("SRM_Claudes_Plan_02.pptx", "SRM_Claudes_Plan_02.pdf"),
    ("CollegeName_TeamName_Submission.pptx", "CollegeName_TeamName_Submission.pdf"),
]

try:
    powerpoint = win32.Dispatch("PowerPoint.Application")
    for pptx_name, pdf_name in pairs:
        pptx_path = os.path.abspath(pptx_name)
        pdf_path = os.path.abspath(pdf_name)
        if os.path.exists(pptx_path):
            deck = powerpoint.Presentations.Open(pptx_path, WithWindow=False)
            deck.SaveAs(pdf_path, 32) # 32 = ppSaveAsPDF
            deck.Close()
            print("SUCCESS: Exported PDF at", pdf_path)
    powerpoint.Quit()
except Exception as e:
    print("Note: Direct PDF export via COM:", e)

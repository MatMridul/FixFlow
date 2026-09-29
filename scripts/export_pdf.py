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

pptx_path = os.path.abspath("SRMIST_FixFlow_Submission.pptx")
pdf_path = os.path.abspath("SRMIST_FixFlow_Submission.pdf")

try:
    powerpoint = win32.Dispatch("PowerPoint.Application")
    deck = powerpoint.Presentations.Open(pptx_path, WithWindow=False)
    deck.SaveAs(pdf_path, 32) # 32 = ppSaveAsPDF
    deck.Close()
    powerpoint.Quit()
    print("SUCCESS: Exported PDF at", pdf_path)
except Exception as e:
    print("Note: Direct PDF export via COM:", e)

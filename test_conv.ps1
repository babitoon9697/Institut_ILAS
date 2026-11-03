
 = 'C:\Users\INSTITUT ILAS\Desktop\Registre_General_Maternelle_ILAS.docx'
 = 'C:\Users\INSTITUT ILAS\Desktop\test_word_export.pdf'
 = New-Object -ComObject Word.Application
.Visible = False
 = .Documents.Open()
.SaveAs([ref], [ref]17)
.Close()
.Quit()
Write-Host 'Word export success:' (Test-Path )

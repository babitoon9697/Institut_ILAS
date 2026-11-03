
$docxPath = "C:\Users\INSTITUT ILAS\Desktop\Registre_General_Maternelle_Association_Dream.docx"
$pdfPath = "C:\Users\INSTITUT ILAS\Desktop\Registre_General_Maternelle_Association_Dream.pdf"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open($docxPath)
    $doc.SaveAs([ref]$pdfPath, [ref]17)
    $doc.Close()
    Write-Output "SUCCESS"
} catch {
    Write-Output "ERROR: $_"
} finally {
    $word.Quit()
}

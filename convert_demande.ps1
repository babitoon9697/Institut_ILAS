
$word = New-Object -ComObject Word.Application
$word.Visible = $false
try {
    $doc = $word.Documents.Open("C:\Users\INSTITUT ILAS\Desktop\Demande_Code_Massar_Association_Dream.docx")
    $doc.SaveAs([ref]"C:\Users\INSTITUT ILAS\Desktop\Demande_Code_Massar_Association_Dream.pdf", [ref]17)
    $doc.Close()
    Write-Output "SUCCESS"
} catch {
    Write-Output "ERROR: $_"
} finally {
    $word.Quit()
}

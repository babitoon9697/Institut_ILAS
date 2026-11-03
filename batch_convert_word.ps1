$word = New-Object -ComObject Word.Application
$word.Visible = $false

try {
    $doc = $word.Documents.Open("C:\\Users\\INSTITUT ILAS\\Desktop\\Registre_General_Maternelle_Association_Dream.docx")
    $doc.SaveAs([ref]"C:\\Users\\INSTITUT ILAS\\Desktop\\Registre_General_Maternelle_Association_Dream.pdf", [ref]17)
    $doc.Close()
    Write-Output "Converted: Registre_General_Maternelle_Association_Dream.pdf"
} catch {
    Write-Output "Error on Registre_General_Maternelle_Association_Dream.pdf: $_"
}


try {
    $doc = $word.Documents.Open("C:\\Users\\INSTITUT ILAS\\Desktop\\Registre_Grande_Section_Association_Dream.docx")
    $doc.SaveAs([ref]"C:\\Users\\INSTITUT ILAS\\Desktop\\Registre_Grande_Section_Association_Dream.pdf", [ref]17)
    $doc.Close()
    Write-Output "Converted: Registre_Grande_Section_Association_Dream.pdf"
} catch {
    Write-Output "Error on Registre_Grande_Section_Association_Dream.pdf: $_"
}


try {
    $doc = $word.Documents.Open("C:\\Users\\INSTITUT ILAS\\Desktop\\Registre_Moyenne_Section_Association_Dream.docx")
    $doc.SaveAs([ref]"C:\\Users\\INSTITUT ILAS\\Desktop\\Registre_Moyenne_Section_Association_Dream.pdf", [ref]17)
    $doc.Close()
    Write-Output "Converted: Registre_Moyenne_Section_Association_Dream.pdf"
} catch {
    Write-Output "Error on Registre_Moyenne_Section_Association_Dream.pdf: $_"
}


try {
    $doc = $word.Documents.Open("C:\\Users\\INSTITUT ILAS\\Desktop\\Registre_Petite_Section_Association_Dream.docx")
    $doc.SaveAs([ref]"C:\\Users\\INSTITUT ILAS\\Desktop\\Registre_Petite_Section_Association_Dream.pdf", [ref]17)
    $doc.Close()
    Write-Output "Converted: Registre_Petite_Section_Association_Dream.pdf"
} catch {
    Write-Output "Error on Registre_Petite_Section_Association_Dream.pdf: $_"
}

$word.Quit()
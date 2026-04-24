$headers = @{ 'Content-Type' = 'application/json' }
$url = "http://localhost:8000/evaluate_advanced"

$A = ConvertTo-Json -Depth 8 @{
  state = @{ bases = @(@{ name="Arktholm (Capital X)"; x=418.3; y=95.0; inventory=@{ "patriot-pac3"=60; "nasams"=100 } }) }
  threats = @(
    @{ id="BM-01"; x=418.3; y=195.0; speed_kmh=3000; estimated_type="ballistic"; threat_value=400 }
    @{ id="BM-02"; x=350.0; y=165.0; speed_kmh=3500; estimated_type="ballistic"; threat_value=400 }
    @{ id="BM-03"; x=490.0; y=175.0; speed_kmh=2800; estimated_type="ballistic"; threat_value=350 }
  )
  doctrine_primary="balanced"; use_rl=$true; run_mc=$true
}
$rA = Invoke-RestMethod -Method POST -Uri $url -Body $A -Headers $headers
Write-Host ""; Write-Host "=== SCENARIO A : Ballistic Strike (3 BMs, BALANCED) ==="
Write-Host "  Score: $($rA.strategic_consequence_score)  Leaked: $($rA.leaked)  Assignments: $($rA.tactical_assignments.Count)"
if ($rA.mc_metrics) { Write-Host "  MC: Surv=$($rA.mc_metrics.survival_rate_pct)% Int=$($rA.mc_metrics.intercept_rate_pct)% Mean=$($rA.mc_metrics.mean_score)" }
$rA.tactical_assignments | ForEach-Object { Write-Host "    $($_.threat_id) -> $($_.effector) @ $($_.base)" }

$B = ConvertTo-Json -Depth 8 @{
  state = @{ bases = @(
    @{ name="Arktholm (Capital X)"; x=418.3; y=95.0; inventory=@{"patriot-pac3"=60;"nasams"=100;"coyote-block2"=200} }
    @{ name="Northern Vanguard Base"; x=198.3; y=335.0; inventory=@{"patriot-pac3"=60;"nasams"=100;"coyote-block2"=200} }
    @{ name="Highridge Command"; x=838.3; y=75.0; inventory=@{"patriot-pac3"=60;"nasams"=100} }
    @{ name="Nordvik"; x=140.0; y=323.3; inventory=@{"patriot-pac3"=60;"nasams"=100} }
  )}
  threats = @(
    @{ id="D-01"; x=198.3; y=355.0; speed_kmh=200;  estimated_type="drone";         threat_value=25  }
    @{ id="D-02"; x=180.0; y=362.0; speed_kmh=220;  estimated_type="drone";         threat_value=25  }
    @{ id="D-03"; x=215.0; y=358.0; speed_kmh=190;  estimated_type="drone";         threat_value=20  }
    @{ id="C-01"; x=418.3; y=180.0; speed_kmh=900;  estimated_type="cruise-missile";threat_value=250 }
    @{ id="C-02"; x=380.0; y=170.0; speed_kmh=900;  estimated_type="cruise-missile";threat_value=200 }
    @{ id="F-01"; x=838.3; y=165.0; speed_kmh=1800; estimated_type="fighter";       threat_value=300 }
    @{ id="H-01"; x=418.3; y=185.0; speed_kmh=6000; estimated_type="hypersonic-pgm";threat_value=500 }
  )
  doctrine_primary="layered"; use_rl=$true; run_mc=$true
}
$rB = Invoke-RestMethod -Method POST -Uri $url -Body $B -Headers $headers
Write-Host ""; Write-Host "=== SCENARIO B : Swarm + Fast Mover (7 threats, LAYERED) ==="
Write-Host "  Score: $($rB.strategic_consequence_score)  Leaked: $($rB.leaked)  Assignments: $($rB.tactical_assignments.Count)"
if ($rB.mc_metrics) { Write-Host "  MC: Surv=$($rB.mc_metrics.survival_rate_pct)% Int=$($rB.mc_metrics.intercept_rate_pct)% Mean=$($rB.mc_metrics.mean_score)" }
$rB.tactical_assignments | ForEach-Object { Write-Host "    $($_.threat_id) -> $($_.effector) @ $($_.base)" }

$C = ConvertTo-Json -Depth 8 @{
  state = @{ bases = @(
    @{ name="Arktholm (Capital X)"; x=418.3; y=95.0; inventory=@{"patriot-pac3"=60;"nasams"=100;"coyote-block2"=200} }
    @{ name="Highridge Command"; x=838.3; y=75.0; inventory=@{"patriot-pac3"=60;"nasams"=100} }
  )}
  threats = @(
    @{ id="H-01"; x=418.3; y=195.0; speed_kmh=7000; estimated_type="hypersonic-pgm"; threat_value=500 }
    @{ id="H-02"; x=390.0; y=185.0; speed_kmh=6500; estimated_type="hypersonic-pgm"; threat_value=500 }
    @{ id="H-03"; x=838.3; y=165.0; speed_kmh=7000; estimated_type="hypersonic-pgm"; threat_value=500 }
    @{ id="C-01"; x=800.0; y=160.0; speed_kmh=900;  estimated_type="cruise-missile"; threat_value=250 }
    @{ id="C-02"; x=870.0; y=168.0; speed_kmh=900;  estimated_type="cruise-missile"; threat_value=250 }
    @{ id="DC-1"; x=418.3; y=175.0; speed_kmh=300;  estimated_type="decoy";          threat_value=5   }
    @{ id="DC-2"; x=838.3; y=155.0; speed_kmh=310;  estimated_type="decoy";          threat_value=5   }
  )
  doctrine_primary="aggressive"; use_rl=$true; run_mc=$true
}
$rC = Invoke-RestMethod -Method POST -Uri $url -Body $C -Headers $headers
Write-Host ""; Write-Host "=== SCENARIO C : Saturation + Decoys (7 threats, AGGRESSIVE) ==="
Write-Host "  Score: $($rC.strategic_consequence_score)  Leaked: $($rC.leaked)  Assignments: $($rC.tactical_assignments.Count)"
if ($rC.mc_metrics) { Write-Host "  MC: Surv=$($rC.mc_metrics.survival_rate_pct)% Int=$($rC.mc_metrics.intercept_rate_pct)% Mean=$($rC.mc_metrics.mean_score)" }
$rC.tactical_assignments | ForEach-Object { Write-Host "    $($_.threat_id) -> $($_.effector) @ $($_.base)" }

Write-Host ""; Write-Host "=== ALL 3 SCENARIOS COMPLETE via /evaluate_advanced ==="
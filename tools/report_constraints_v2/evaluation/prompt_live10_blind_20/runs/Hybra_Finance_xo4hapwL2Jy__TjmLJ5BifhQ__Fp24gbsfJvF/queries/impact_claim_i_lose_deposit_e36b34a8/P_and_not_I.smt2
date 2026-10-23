; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6606dda5_total_assets () Int)
(declare-fun c6606dda5_total_supply () Int)
(declare-fun c6606dda5_victim_deposit_lost () Bool)
(declare-fun c6606dda5_victim_shares_minted () Int)
(assert
 (= c6606dda5_total_assets c6606dda5_total_assets))
(assert
 (= c6606dda5_total_supply c6606dda5_total_supply))
(assert
 (= c6606dda5_victim_deposit_lost c6606dda5_victim_deposit_lost))
(assert
 (= c6606dda5_victim_shares_minted c6606dda5_victim_shares_minted))
(define-fun report_preconditions () Bool (and (= 1 c6606dda5_total_supply) (<= 1 c6606dda5_total_assets)))
(define-fun report_safety () Bool (=> (and (= 1 c6606dda5_total_supply) (<= 1 c6606dda5_total_assets))
    (and (< 0 c6606dda5_victim_shares_minted)
         (not c6606dda5_victim_deposit_lost))))
(define-fun report_effects () Bool (and (= 1 c6606dda5_total_supply)
     (<= 1 c6606dda5_total_assets)
     (not (and (< 0 c6606dda5_victim_shares_minted)
               (not c6606dda5_victim_deposit_lost)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)

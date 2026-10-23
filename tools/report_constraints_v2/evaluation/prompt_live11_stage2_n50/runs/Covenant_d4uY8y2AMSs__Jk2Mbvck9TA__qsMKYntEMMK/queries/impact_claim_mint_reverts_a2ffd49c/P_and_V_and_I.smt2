; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c6cd9efcd_etwap_updated_before_cap_check () Bool)
(declare-fun c6cd9efcd_last_etwap_base_supply () Int)
(declare-fun c6cd9efcd_mint_reverted_cap_exceeded () Bool)
(declare-fun c6cd9efcd_mint_within_supply_bound () Bool)
(assert
 (= c6cd9efcd_etwap_updated_before_cap_check c6cd9efcd_etwap_updated_before_cap_check))
(assert
 (= c6cd9efcd_last_etwap_base_supply c6cd9efcd_last_etwap_base_supply))
(assert
 (= c6cd9efcd_mint_reverted_cap_exceeded c6cd9efcd_mint_reverted_cap_exceeded))
(assert
 (= c6cd9efcd_mint_within_supply_bound c6cd9efcd_mint_within_supply_bound))
(define-fun report_preconditions () Bool (and (= 0 c6cd9efcd_last_etwap_base_supply)
     (not c6cd9efcd_etwap_updated_before_cap_check)))
(define-fun report_safety () Bool (=> (and (= 0 c6cd9efcd_last_etwap_base_supply)
         (not c6cd9efcd_etwap_updated_before_cap_check)
         c6cd9efcd_mint_within_supply_bound)
    (not c6cd9efcd_mint_reverted_cap_exceeded)))
(define-fun report_effects () Bool (and (= 0 c6cd9efcd_last_etwap_base_supply)
     (not c6cd9efcd_etwap_updated_before_cap_check)
     c6cd9efcd_mint_within_supply_bound
     (not (not c6cd9efcd_mint_reverted_cap_exceeded))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)

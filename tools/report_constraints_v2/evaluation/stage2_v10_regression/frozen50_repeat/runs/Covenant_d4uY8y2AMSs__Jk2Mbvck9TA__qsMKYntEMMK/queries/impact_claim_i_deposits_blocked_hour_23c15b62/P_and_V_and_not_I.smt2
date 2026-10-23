; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3de5cc01_deposits_blocked () Bool)
(declare-fun c3de5cc01_deposits_blocked_duration_minutes () Int)
(declare-fun c3de5cc01_first_mint_updates_twap () Bool)
(declare-fun c3de5cc01_last_etwap_base_supply () Int)
(assert
 (= c3de5cc01_deposits_blocked c3de5cc01_deposits_blocked))
(assert
 (= c3de5cc01_deposits_blocked_duration_minutes c3de5cc01_deposits_blocked_duration_minutes))
(assert
 (= c3de5cc01_first_mint_updates_twap c3de5cc01_first_mint_updates_twap))
(assert
 (= c3de5cc01_last_etwap_base_supply c3de5cc01_last_etwap_base_supply))
(define-fun report_preconditions () Bool (and (= 0 c3de5cc01_last_etwap_base_supply)
     (not c3de5cc01_first_mint_updates_twap)))
(define-fun report_safety () Bool (=> (and (= 0 c3de5cc01_last_etwap_base_supply)
         (not c3de5cc01_first_mint_updates_twap))
    (or (not c3de5cc01_deposits_blocked)
        (> 60 c3de5cc01_deposits_blocked_duration_minutes))))
(define-fun report_effects () Bool (and (= 0 c3de5cc01_last_etwap_base_supply)
     (not c3de5cc01_first_mint_updates_twap)
     (not (or (not c3de5cc01_deposits_blocked)
              (> 60 c3de5cc01_deposits_blocked_duration_minutes)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)

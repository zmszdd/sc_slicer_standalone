; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c253006f5_last_etwap_base_supply () Int)
(declare-fun c253006f5_mint_cap_revert_occurred () Bool)
(declare-fun c253006f5_subsequent_mint_attempted () Bool)
(declare-fun c253006f5_threshold_crossed () Bool)
(assert
 (= c253006f5_last_etwap_base_supply c253006f5_last_etwap_base_supply))
(assert
 (= c253006f5_mint_cap_revert_occurred c253006f5_mint_cap_revert_occurred))
(assert
 (= c253006f5_subsequent_mint_attempted c253006f5_subsequent_mint_attempted))
(assert
 (= c253006f5_threshold_crossed c253006f5_threshold_crossed))
(define-fun report_preconditions () Bool (and (= 0 c253006f5_last_etwap_base_supply) c253006f5_threshold_crossed))
(define-fun report_safety () Bool (=> (and c253006f5_threshold_crossed c253006f5_subsequent_mint_attempted)
    (not c253006f5_mint_cap_revert_occurred)))
(define-fun report_effects () Bool (and c253006f5_threshold_crossed
     c253006f5_subsequent_mint_attempted
     (not (not c253006f5_mint_cap_revert_occurred))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)

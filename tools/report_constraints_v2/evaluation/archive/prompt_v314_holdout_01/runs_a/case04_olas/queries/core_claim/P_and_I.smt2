; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun twap_equals_spot () Bool)
(declare-fun amount_out_min_zero () Bool)
(declare-fun buybacker_holds_secondtokens () Bool)
(declare-fun buyback_permissionless () Bool)
(declare-fun buyback_completes () Bool)
(assert
 (= twap_equals_spot twap_equals_spot))
(assert
 (= amount_out_min_zero amount_out_min_zero))
(assert
 (= buybacker_holds_secondtokens buybacker_holds_secondtokens))
(assert
 (= buyback_permissionless buyback_permissionless))
(assert
 (= buyback_completes buyback_completes))
(define-fun report_preconditions () Bool (and buybacker_holds_secondtokens
     twap_equals_spot
     amount_out_min_zero
     buyback_permissionless))
(define-fun report_safety () Bool (=> (and twap_equals_spot amount_out_min_zero buybacker_holds_secondtokens)
    (not buyback_completes)))
(define-fun report_effects () Bool (and twap_equals_spot
     amount_out_min_zero
     buybacker_holds_secondtokens
     buyback_completes))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)

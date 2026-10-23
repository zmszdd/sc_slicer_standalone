; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7cd3d738_deposits_blocked_flag () Bool)
(declare-fun c7cd3d738_etwap_base_supply () Int)
(declare-fun c7cd3d738_etwap_updated_before_cap_check () Bool)
(assert
 (= c7cd3d738_deposits_blocked_flag c7cd3d738_deposits_blocked_flag))
(assert
 (= c7cd3d738_etwap_base_supply c7cd3d738_etwap_base_supply))
(assert
 (= c7cd3d738_etwap_updated_before_cap_check c7cd3d738_etwap_updated_before_cap_check))
(define-fun report_preconditions () Bool (and (= 0 c7cd3d738_etwap_base_supply)
     (not c7cd3d738_etwap_updated_before_cap_check)))
(define-fun report_safety () Bool (=> (and (= 0 c7cd3d738_etwap_base_supply)
         (not c7cd3d738_etwap_updated_before_cap_check))
    (not c7cd3d738_deposits_blocked_flag)))
(define-fun report_effects () Bool (and (= 0 c7cd3d738_etwap_base_supply)
     (not c7cd3d738_etwap_updated_before_cap_check)
     (not (not c7cd3d738_deposits_blocked_flag))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)

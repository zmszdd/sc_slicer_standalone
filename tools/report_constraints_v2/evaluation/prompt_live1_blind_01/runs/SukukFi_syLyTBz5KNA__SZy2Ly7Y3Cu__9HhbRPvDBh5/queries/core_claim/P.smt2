; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun victim_self_allowance_set () Bool)
(declare-fun caller_owner_allowance_absent () Bool)
(declare-fun assets_transferred_to_attacker_occurred () Bool)
(assert
 (= victim_self_allowance_set victim_self_allowance_set))
(assert
 (= caller_owner_allowance_absent caller_owner_allowance_absent))
(assert
 (= assets_transferred_to_attacker_occurred assets_transferred_to_attacker_occurred))
(define-fun report_preconditions () Bool (and victim_self_allowance_set caller_owner_allowance_absent))
(define-fun report_safety () Bool (=> (and victim_self_allowance_set caller_owner_allowance_absent)
    (not assets_transferred_to_attacker_occurred)))
(define-fun report_effects () Bool (and victim_self_allowance_set
     caller_owner_allowance_absent
     (not (not assets_transferred_to_attacker_occurred))))
(assert report_preconditions)
(check-sat)
(get-model)

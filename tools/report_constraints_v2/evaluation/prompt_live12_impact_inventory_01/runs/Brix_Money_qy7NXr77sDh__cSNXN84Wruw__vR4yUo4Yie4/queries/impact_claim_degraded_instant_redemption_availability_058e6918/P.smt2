; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc0e1b960_buffer_stripped_to_target () Bool)
(declare-fun cc0e1b960_caller_is_owner () Bool)
(declare-fun cc0e1b960_documented_owner_only () Bool)
(declare-fun cc0e1b960_vault_balance_exceeds_target () Bool)
(assert
 (= cc0e1b960_buffer_stripped_to_target cc0e1b960_buffer_stripped_to_target))
(assert
 (= cc0e1b960_caller_is_owner cc0e1b960_caller_is_owner))
(assert
 (= cc0e1b960_documented_owner_only cc0e1b960_documented_owner_only))
(assert
 (= cc0e1b960_vault_balance_exceeds_target cc0e1b960_vault_balance_exceeds_target))
(define-fun report_preconditions () Bool (and cc0e1b960_vault_balance_exceeds_target cc0e1b960_documented_owner_only))
(define-fun report_safety () Bool (=> (and cc0e1b960_vault_balance_exceeds_target
         cc0e1b960_documented_owner_only
         (not cc0e1b960_caller_is_owner))
    (not cc0e1b960_buffer_stripped_to_target)))
(define-fun report_effects () Bool (and cc0e1b960_vault_balance_exceeds_target
     cc0e1b960_documented_owner_only
     (not cc0e1b960_caller_is_owner)
     (not (not cc0e1b960_buffer_stripped_to_target))))
(assert report_preconditions)
(check-sat)
(get-model)

; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cdcf3375a_accountant_is_configured () Bool)
(declare-fun cdcf3375a_active_registration_exists () Bool)
(declare-fun cdcf3375a_hypercore_activation_asynchronous () Bool)
(declare-fun cdcf3375a_registration_promoted_after_successful_read () Bool)
(declare-fun cdcf3375a_total_backing_signed_reverts () Bool)
(assert
 (= cdcf3375a_accountant_is_configured cdcf3375a_accountant_is_configured))
(assert
 (= cdcf3375a_active_registration_exists cdcf3375a_active_registration_exists))
(assert
 (= cdcf3375a_hypercore_activation_asynchronous cdcf3375a_hypercore_activation_asynchronous))
(assert
 (= cdcf3375a_registration_promoted_after_successful_read cdcf3375a_registration_promoted_after_successful_read))
(assert
 (= cdcf3375a_total_backing_signed_reverts cdcf3375a_total_backing_signed_reverts))
(define-fun report_preconditions () Bool (and cdcf3375a_accountant_is_configured
     (not cdcf3375a_active_registration_exists)))
(define-fun report_safety () Bool (=> cdcf3375a_hypercore_activation_asynchronous
    cdcf3375a_registration_promoted_after_successful_read))
(define-fun report_effects () Bool (and cdcf3375a_total_backing_signed_reverts
     cdcf3375a_total_backing_signed_reverts))

; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd9de5f8b_accountant_is_configured () Bool)
(declare-fun cd9de5f8b_active_registration_exists () Bool)
(declare-fun cd9de5f8b_distributable_surplus_succeeds () Bool)
(declare-fun cd9de5f8b_hypercore_slot_active () Bool)
(assert
 (= cd9de5f8b_accountant_is_configured cd9de5f8b_accountant_is_configured))
(assert
 (= cd9de5f8b_active_registration_exists cd9de5f8b_active_registration_exists))
(assert
 (= cd9de5f8b_distributable_surplus_succeeds cd9de5f8b_distributable_surplus_succeeds))
(assert
 (= cd9de5f8b_hypercore_slot_active cd9de5f8b_hypercore_slot_active))
(define-fun report_preconditions () Bool (and cd9de5f8b_accountant_is_configured
     (not cd9de5f8b_active_registration_exists)
     (not cd9de5f8b_hypercore_slot_active)))
(define-fun report_safety () Bool (=> (not cd9de5f8b_distributable_surplus_succeeds)
    (=> (and cd9de5f8b_accountant_is_configured
             (not cd9de5f8b_active_registration_exists)
             (not cd9de5f8b_hypercore_slot_active))
        cd9de5f8b_distributable_surplus_succeeds)))
(define-fun report_effects () Bool (and (not cd9de5f8b_distributable_surplus_succeeds)
     cd9de5f8b_accountant_is_configured
     (not cd9de5f8b_active_registration_exists)
     (not cd9de5f8b_hypercore_slot_active)
     (not cd9de5f8b_distributable_surplus_succeeds)))

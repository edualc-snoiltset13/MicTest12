package com.abc_bank.abc_bank.auth_users.controller;

import com.abc_bank.abc_bank.auth_users.dtos.LoginRequest;
import com.abc_bank.abc_bank.auth_users.dtos.LoginResponse;
import com.abc_bank.abc_bank.auth_users.dtos.RegistrationRequest;
import com.abc_bank.abc_bank.auth_users.dtos.ResetPasswordRequest;
import com.abc_bank.abc_bank.auth_users.dtos.UserDTO;
import com.abc_bank.abc_bank.auth_users.services.UserService;
import com.abc_bank.abc_bank.exceptions.BadRequestException;
import com.abc_bank.abc_bank.res.Response;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final UserService userService;

    @PostMapping("/register")
    public ResponseEntity<Response<UserDTO>> register(@Valid @RequestBody RegistrationRequest request) {
        Response<UserDTO> response = userService.registerUser(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @PostMapping("/login")
    public ResponseEntity<Response<LoginResponse>> login(@Valid @RequestBody LoginRequest request) {
        return ResponseEntity.ok(userService.loginUser(request));
    }

    @PostMapping("/password-reset/request")
    public ResponseEntity<Response<?>> requestPasswordReset(@RequestParam("email") String email) {
        if (email == null || email.isBlank()) {
            throw new BadRequestException("email is required");
        }
        return ResponseEntity.ok(userService.requestPasswordReset(email));
    }

    @PostMapping("/password-reset/confirm")
    public ResponseEntity<Response<?>> confirmPasswordReset(@Valid @RequestBody ResetPasswordRequest request) {
        return ResponseEntity.ok(userService.resetPassword(request));
    }
}

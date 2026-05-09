package com.abc_bank.abc_bank.auth_users.dtos;


import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

import java.util.List;

@Data
public class RegistrationRequest {

    @NotBlank(message="firstname is required")
    private String firstName;

    private String lastName;
    @NotBlank(message="email is required")
    @Email
    private String email;

    private List<String> roles;

    @NotBlank(message="password is required")
    private String password;
}
